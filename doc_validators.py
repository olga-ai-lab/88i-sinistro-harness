"""
doc_validators.py — Camada determinística de validação forense (Semana 4.5)

Executa ANTES do Claude no pipeline documental.
Objetivo: detectar fraudes óbvias com custo zero de LLM e fornecer
sinais estruturados que enriquecem o contexto do forensics.

Validadores implementados:
  1. EXIF/metadados de imagem    — software de edição, data de criação
  2. Metadados de PDF            — criado com, revisões, datas
  3. Checksums brasileiros       — CPF, CNPJ, RENAVAM (algorítmicos)
  4. Validação de CRM            — API CFM (com fallback offline)
  5. Chave NF-e                  — estrutura 44 dígitos + dígito verificador
  6. Error Level Analysis (ELA)  — detecta regiões editadas em imagens JPEG

Cada validador retorna uma lista de SinalForense.
O SinalForense é injetado no contexto do Claude (forensics) e no VeredictoCobertura.

Princípios:
  - ZERO LLM — tudo determinístico e auditável
  - Fail-open: erro num validador NÃO bloqueia o pipeline
  - Cada sinal carrega código, severidade e evidência concreta
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import httpx


# ============================================================
# Tipo de sinal forense
# ============================================================

@dataclass
class SinalForense:
    codigo: str          # ex: "EXIF_EDIT_SOFTWARE", "CPF_INVALIDO"
    severidade: str      # "baixa" | "media" | "alta" | "critica"
    descricao: str       # texto humano para o analista
    evidencia: str       # dado concreto que sustenta o sinal
    validador: str       # qual validador emitiu


@dataclass
class ResultadoValidacao:
    sinais: list[SinalForense] = field(default_factory=list)
    resumo: str = "ok"
    passou: bool = True   # False se qualquer sinal for alta/critica

    def adicionar(self, sinal: SinalForense):
        self.sinais.append(sinal)
        if sinal.severidade in ("alta", "critica"):
            self.passou = False
        if self.resumo == "ok":
            self.resumo = sinal.descricao
        else:
            self.resumo = f"{len(self.sinais)} sinais detectados"


# ============================================================
# 1. Validador EXIF (imagens)
# ============================================================

# Software de edição conhecidos — presença é red flag em documentos "originais"
_EDIT_SOFTWARE = {
    "photoshop", "gimp", "lightroom", "paint.net", "affinity",
    "canva", "pixelmator", "snapseed", "picsart", "facetune",
    "adobe", "corel", "inkscape",
}

def validar_exif(dados: bytes, nome_arquivo: str) -> ResultadoValidacao:
    """
    Verifica metadados EXIF de imagens JPEG/TIFF.
    Detecta: software de edição, inconsistências de data, GPS removido.
    """
    resultado = ResultadoValidacao()

    try:
        import piexif
    except ImportError:
        return resultado  # fail-open

    try:
        exif = piexif.load(dados)
    except Exception:
        return resultado  # sem EXIF — não é sinal por si só

    # Software usado para criar/editar
    software_raw = exif.get("0th", {}).get(piexif.ImageIFD.Software, b"")
    if isinstance(software_raw, bytes):
        software = software_raw.decode("utf-8", errors="replace").strip()
    else:
        software = str(software_raw)

    if software:
        software_lower = software.lower()
        if any(ed in software_lower for ed in _EDIT_SOFTWARE):
            resultado.adicionar(SinalForense(
                codigo="EXIF_EDIT_SOFTWARE",
                severidade="alta",
                descricao=f"Imagem criada/editada com software de edição: {software}",
                evidencia=software,
                validador="exif",
            ))

    # Data de modificação vs. data de criação (inconsistência)
    dt_orig = exif.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal, b"")
    dt_digit = exif.get("Exif", {}).get(piexif.ExifIFD.DateTimeDigitized, b"")
    dt_modi = exif.get("0th", {}).get(piexif.ImageIFD.DateTime, b"")

    def _decode_dt(v):
        if isinstance(v, bytes):
            return v.decode("utf-8", errors="replace").strip()
        return str(v) if v else ""

    dt_orig_s = _decode_dt(dt_orig)
    dt_modi_s = _decode_dt(dt_modi)

    if dt_orig_s and dt_modi_s and dt_orig_s != dt_modi_s:
        resultado.adicionar(SinalForense(
            codigo="EXIF_DATE_MISMATCH",
            severidade="media",
            descricao=f"Data original ({dt_orig_s}) difere da data de modificação ({dt_modi_s})",
            evidencia=f"original={dt_orig_s} | modificado={dt_modi_s}",
            validador="exif",
        ))

    # Ausência total de EXIF em foto de smartphone é suspeita
    # (smartphones sempre geram EXIF com make/model)
    make = exif.get("0th", {}).get(piexif.ImageIFD.Make, b"")
    model = exif.get("0th", {}).get(piexif.ImageIFD.Model, b"")
    if not make and not model and not software:
        resultado.adicionar(SinalForense(
            codigo="EXIF_STRIPPED",
            severidade="baixa",
            descricao="EXIF de câmera/dispositivo removido — pode indicar edição prévia",
            evidencia="make=vazio, model=vazio, software=vazio",
            validador="exif",
        ))

    return resultado


# ============================================================
# 2. Validador de PDF
# ============================================================

_PDF_EDIT_PRODUCERS = {
    "pdfedit", "foxit phantom", "nitro", "sejda", "smallpdf",
    "ilovepdf", "adobe acrobat", "libreoffice draw",
}

def validar_pdf(dados: bytes, nome_arquivo: str) -> ResultadoValidacao:
    """
    Verifica metadados de PDFs.
    Detecta: software de edição, número de revisões, datas suspeitas.
    """
    resultado = ResultadoValidacao()

    try:
        import pypdf
    except ImportError:
        return resultado

    try:
        reader = pypdf.PdfReader(io.BytesIO(dados))
        meta = reader.metadata or {}
    except Exception as e:
        resultado.adicionar(SinalForense(
            codigo="PDF_PARSE_ERROR",
            severidade="media",
            descricao=f"PDF não pôde ser lido: {e}",
            evidencia=str(e),
            validador="pdf",
        ))
        return resultado

    # Producer / Creator
    producer = str(meta.get("/Producer", "")).strip()
    creator = str(meta.get("/Creator", "")).strip()

    for campo, valor in [("Producer", producer), ("Creator", creator)]:
        if valor:
            valor_lower = valor.lower()
            if any(ed in valor_lower for ed in _PDF_EDIT_PRODUCERS):
                resultado.adicionar(SinalForense(
                    codigo="PDF_EDIT_TOOL",
                    severidade="alta",
                    descricao=f"PDF gerado/editado com ferramenta suspeita: {valor}",
                    evidencia=f"{campo}={valor}",
                    validador="pdf",
                ))

    # Número de revisões (ModDate diferente de CreationDate → editado)
    creation = str(meta.get("/CreationDate", "")).strip()
    mod_date = str(meta.get("/ModDate", "")).strip()

    if creation and mod_date and creation != mod_date:
        resultado.adicionar(SinalForense(
            codigo="PDF_MODIFIED",
            severidade="media",
            descricao=f"PDF foi modificado após criação original",
            evidencia=f"criado={creation} | modificado={mod_date}",
            validador="pdf",
        ))

    # Número de páginas suspeito para o tipo de documento
    n_pages = len(reader.pages)
    if n_pages == 0:
        resultado.adicionar(SinalForense(
            codigo="PDF_EMPTY",
            severidade="alta",
            descricao="PDF sem páginas — arquivo corrompido ou manipulado",
            evidencia=f"pages={n_pages}",
            validador="pdf",
        ))

    return resultado


# ============================================================
# 3. Checksums brasileiros
# ============================================================

def _cpf_valido(cpf: str) -> bool:
    """Valida CPF pelo algoritmo de dígitos verificadores."""
    digits = re.sub(r"\D", "", cpf)
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    # Dígito 1
    s = sum(int(digits[i]) * (10 - i) for i in range(9))
    d1 = (s * 10 % 11) % 10
    if d1 != int(digits[9]):
        return False
    # Dígito 2
    s = sum(int(digits[i]) * (11 - i) for i in range(10))
    d2 = (s * 10 % 11) % 10
    return d2 == int(digits[10])


def _cnpj_valido(cnpj: str) -> bool:
    """Valida CNPJ pelo algoritmo de dígitos verificadores."""
    digits = re.sub(r"\D", "", cnpj)
    if len(digits) != 14 or len(set(digits)) == 1:
        return False
    def _calc(d, weights):
        s = sum(int(d[i]) * weights[i] for i in range(len(weights)))
        r = s % 11
        return 0 if r < 2 else 11 - r
    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    return (
        _calc(digits, w1) == int(digits[12])
        and _calc(digits, w2) == int(digits[13])
    )


def _renavam_valido(renavam: str) -> bool:
    """Valida RENAVAM (11 dígitos) pelo algoritmo DETRAN."""
    digits = re.sub(r"\D", "", renavam)
    if len(digits) not in (9, 11):
        return False
    if len(digits) == 9:
        digits = "00" + digits
    weights = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s = sum(int(digits[i]) * weights[i] for i in range(10))
    r = s % 11
    d = 0 if r < 2 else 11 - r
    return d == int(digits[10])


def _chave_nfe_valida(chave: str) -> bool:
    """Valida a chave de acesso NF-e (44 dígitos, com dígito verificador módulo 11)."""
    digits = re.sub(r"\D", "", chave)
    if len(digits) != 44:
        return False
    # Pesos: 2 a 9, ciclicamente da direita para a esquerda
    weights = []
    w = 2
    for _ in range(43):
        weights.append(w)
        w = 2 if w == 9 else w + 1
    weights.reverse()
    s = sum(int(digits[i]) * weights[i] for i in range(43))
    r = s % 11
    d = 0 if r < 2 else 11 - r
    return d == int(digits[43])


def validar_campos_brasileiros(texto: str) -> ResultadoValidacao:
    """
    Extrai CPF, CNPJ, RENAVAM e chaves NF-e do texto e valida checksums.
    Detecta números inválidos — impossível serem legítimos.
    """
    resultado = ResultadoValidacao()

    # CPF
    for m in re.finditer(r"\b\d{3}[.\-]?\d{3}[.\-]?\d{3}[.\-]?\d{2}\b", texto):
        cpf = m.group()
        if not _cpf_valido(cpf):
            resultado.adicionar(SinalForense(
                codigo="CPF_INVALIDO",
                severidade="alta",
                descricao=f"CPF com dígito verificador inválido: {cpf}",
                evidencia=cpf,
                validador="checksum_br",
            ))

    # CNPJ
    for m in re.finditer(r"\b\d{2}[.\-/]?\d{3}[.\-/]?\d{3}[.\-/]?\d{4}[.\-/]?\d{2}\b", texto):
        cnpj = m.group()
        if not _cnpj_valido(cnpj):
            resultado.adicionar(SinalForense(
                codigo="CNPJ_INVALIDO",
                severidade="alta",
                descricao=f"CNPJ com dígito verificador inválido: {cnpj}",
                evidencia=cnpj,
                validador="checksum_br",
            ))

    # RENAVAM (11 dígitos isolados)
    for m in re.finditer(r"\b\d{11}\b", texto):
        candidato = m.group()
        # Evita confundir com chave NF-e ou CPF já validado
        if not _renavam_valido(candidato):
            # Só emite se contexto sugere ser RENAVAM
            if re.search(r"renavam", texto[:m.start() + 50].lower()):
                resultado.adicionar(SinalForense(
                    codigo="RENAVAM_INVALIDO",
                    severidade="alta",
                    descricao=f"RENAVAM com dígito verificador inválido: {candidato}",
                    evidencia=candidato,
                    validador="checksum_br",
                ))

    # Chave NF-e (44 dígitos)
    for m in re.finditer(r"\b\d{44}\b", texto):
        chave = m.group()
        if not _chave_nfe_valida(chave):
            resultado.adicionar(SinalForense(
                codigo="NFE_CHAVE_INVALIDA",
                severidade="critica",
                descricao=f"Chave de acesso NF-e com dígito verificador inválido",
                evidencia=chave,
                validador="checksum_br",
            ))
        else:
            # Chave válida: extrai e valida campos embutidos
            estado = chave[0:2]
            aamm = chave[2:6]
            cnpj_emitente = chave[6:20]
            if not _cnpj_valido(cnpj_emitente):
                resultado.adicionar(SinalForense(
                    codigo="NFE_CNPJ_EMITENTE_INVALIDO",
                    severidade="critica",
                    descricao=f"CNPJ do emitente embutido na chave NF-e é inválido",
                    evidencia=f"cnpj_na_chave={cnpj_emitente}",
                    validador="checksum_br",
                ))

    return resultado


# ============================================================
# 4. Validação de CRM via API CFM
# ============================================================

_CFM_API = "https://sistemas.cfm.org.br/api/v1/medicos/{crm}/{uf}"
_CFM_TIMEOUT = 5  # segundos

def validar_crm(texto: str) -> ResultadoValidacao:
    """
    Extrai CRM + UF do texto e verifica no CFM.
    Padrão: "CRM 45678/SP" ou "CRM: 45678 SP" ou "CRM-SP 45678".

    Fail-open: se a API CFM não responder, não emite sinal de erro.
    """
    resultado = ResultadoValidacao()

    # Extrai padrões de CRM
    # Formatos: "CRM 45678/SP", "CRM 45678 SP", "CRM-SP 45678"
    padrao1 = re.findall(r"CRM[:\s\-]*(\d{4,6})[/\s\-]+([A-Z]{2})", texto.upper())
    padrao2 = re.findall(r"CRM[:\s\-]+([A-Z]{2})[/\s\-]*(\d{4,6})", texto.upper())

    crms = [(num, uf) for num, uf in padrao1]
    crms += [(num, uf) for uf, num in padrao2]

    if not crms:
        # Ausência de CRM em documento médico → sinal
        if re.search(r"laudo|atestado|médic|medic|clínic|clinic|hospital", texto.lower()):
            resultado.adicionar(SinalForense(
                codigo="CRM_AUSENTE",
                severidade="alta",
                descricao="Documento médico sem CRM identificado",
                evidencia="nenhum padrão CRM encontrado no texto",
                validador="crm_cfm",
            ))
        return resultado

    for crm_num, uf in crms:
        # Verifica se a UF é válida
        ufs_validas = {
            "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS",
            "MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC",
            "SP","SE","TO"
        }
        if uf not in ufs_validas:
            resultado.adicionar(SinalForense(
                codigo="CRM_UF_INVALIDA",
                severidade="media",
                descricao=f"UF inválida no CRM: {crm_num}/{uf}",
                evidencia=f"uf={uf}",
                validador="crm_cfm",
            ))
            continue

        # Consulta API CFM
        try:
            url = _CFM_API.format(crm=crm_num, uf=uf)
            resp = httpx.get(url, timeout=_CFM_TIMEOUT)
            if resp.status_code == 404:
                resultado.adicionar(SinalForense(
                    codigo="CRM_NAO_ENCONTRADO",
                    severidade="critica",
                    descricao=f"CRM {crm_num}/{uf} não encontrado no CFM",
                    evidencia=f"HTTP 404 em {url}",
                    validador="crm_cfm",
                ))
            elif resp.status_code == 200:
                data = resp.json()
                situacao = data.get("situacao", "").lower()
                if situacao and situacao not in ("ativo", "regular"):
                    resultado.adicionar(SinalForense(
                        codigo="CRM_IRREGULAR",
                        severidade="alta",
                        descricao=f"CRM {crm_num}/{uf} com situação irregular: {situacao}",
                        evidencia=f"situacao={situacao}",
                        validador="crm_cfm",
                    ))
        except httpx.TimeoutException:
            pass  # fail-open: timeout não bloqueia
        except Exception:
            pass  # fail-open: qualquer erro de rede não bloqueia

    return resultado


# ============================================================
# 5. Error Level Analysis (ELA)
# ============================================================

def validar_ela(dados: bytes, nome_arquivo: str, qualidade: int = 95) -> ResultadoValidacao:
    """
    Error Level Analysis: re-comprime a imagem JPEG em qualidade alta e
    compara com o original. Regiões editadas têm nível de erro diferente.

    Retorna sinal de adulteração se o desvio médio de regiões for alto.
    Limiar: diferença média > 15 é suspeita; > 30 é alta.

    Só funciona com JPEG — para outros formatos retorna silenciosamente.
    """
    resultado = ResultadoValidacao()

    # Só processa JPEG
    ext = Path(nome_arquivo).suffix.lower()
    is_jpeg = ext in (".jpg", ".jpeg") or dados[:2] == b"\xff\xd8"
    if not is_jpeg:
        return resultado

    try:
        from PIL import Image, ImageChops, ImageFilter
        import numpy as np  # type: ignore  # opcional
    except ImportError:
        return resultado

    try:
        original = Image.open(io.BytesIO(dados)).convert("RGB")

        # Re-comprime em qualidade alta
        buffer = io.BytesIO()
        original.save(buffer, format="JPEG", quality=qualidade)
        buffer.seek(0)
        recomprimido = Image.open(buffer).convert("RGB")

        # Diferença pixel a pixel
        diff = ImageChops.difference(original, recomprimido)
        pixels = list(diff.getdata())

        # Calcula média de brilho da diferença
        brilho = [max(r, g, b) for r, g, b in pixels]
        media = sum(brilho) / len(brilho) if brilho else 0
        max_val = max(brilho) if brilho else 0

        if media > 30:
            resultado.adicionar(SinalForense(
                codigo="ELA_ADULTERACAO_ALTA",
                severidade="alta",
                descricao=f"ELA detectou forte evidência de edição (diferença média={media:.1f}, máx={max_val})",
                evidencia=f"ela_mean={media:.2f} ela_max={max_val}",
                validador="ela",
            ))
        elif media > 15:
            resultado.adicionar(SinalForense(
                codigo="ELA_ADULTERACAO_SUSPEITA",
                severidade="media",
                descricao=f"ELA detectou possível edição (diferença média={media:.1f})",
                evidencia=f"ela_mean={media:.2f} ela_max={max_val}",
                validador="ela",
            ))

    except Exception:
        pass  # fail-open

    return resultado


# ============================================================
# Função pública: valida tudo em sequência
# ============================================================

def validar_documento(
    dados: bytes,
    nome_arquivo: str,
    mime_type: str = "application/octet-stream",
    texto_extraido: str = "",
) -> ResultadoValidacao:
    """
    Executa todos os validadores determinísticos no documento.

    Args:
        dados:          bytes do arquivo
        nome_arquivo:   nome original (usado para inferir tipo)
        mime_type:      MIME type do arquivo
        texto_extraido: texto já extraído do doc (para checksums)
                        Se vazio, tenta extrair de PDF/imagem internamente.

    Returns:
        ResultadoValidacao consolidado com todos os sinais.
    """
    resultado = ResultadoValidacao()
    ext = Path(nome_arquivo).suffix.lower()
    is_img = mime_type.startswith("image/") or ext in (".jpg", ".jpeg", ".png", ".tiff", ".bmp")
    is_pdf = mime_type == "application/pdf" or ext == ".pdf"

    # 1. EXIF (imagens)
    if is_img:
        r = validar_exif(dados, nome_arquivo)
        for s in r.sinais:
            resultado.adicionar(s)

    # 2. Metadados PDF
    if is_pdf:
        r = validar_pdf(dados, nome_arquivo)
        for s in r.sinais:
            resultado.adicionar(s)

    # 3. Checksums brasileiros (texto)
    if texto_extraido:
        r = validar_campos_brasileiros(texto_extraido)
        for s in r.sinais:
            resultado.adicionar(s)

    # 4. CRM (texto)
    if texto_extraido:
        r = validar_crm(texto_extraido)
        for s in r.sinais:
            resultado.adicionar(s)

    # 5. ELA (imagens JPEG)
    if is_img:
        r = validar_ela(dados, nome_arquivo)
        for s in r.sinais:
            resultado.adicionar(s)

    if not resultado.sinais:
        resultado.resumo = "nenhum sinal detectado"

    return resultado


def sinais_para_contexto(resultado: ResultadoValidacao) -> str:
    """
    Serializa os sinais forenses em texto estruturado para injetar
    no prompt do Claude (forensics).
    """
    if not resultado.sinais:
        return ""
    linhas = ["## Sinais Forenses Determinísticos (pré-análise)"]
    for s in resultado.sinais:
        linhas.append(
            f"- [{s.severidade.upper()}] {s.codigo}: {s.descricao} | evidência: {s.evidencia}"
        )
    return "\n".join(linhas)
