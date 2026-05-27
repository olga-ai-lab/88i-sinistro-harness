# Operations Team Training Completion Record

**Program Name:** 88i Sinistro Agent Operations Training  
**Program Duration:** 3 sessions (3.5 hours total)  
**Certification Valid:** 12 months from completion  
**Last Updated:** May 27, 2026  
**Program Manager:** Operations Manager  
**Location:** Virtual (Zoom) and hands-on labs

---

## Program Overview

This document tracks completion and certification for the 88i Sinistro Agent operations training program. All engineers must complete all three sessions and pass the competency assessment before joining the on-call rotation.

**Required for On-Call Rotation:**
1. ✅ Complete Session 1: System Overview & Monitoring (1 hour)
2. ✅ Complete Session 2: Incident Response & Runbooks (1.5 hours)
3. ✅ Complete Session 3: Operational Procedures (1 hour)
4. ✅ Pass Knowledge Assessment (80% required)
5. ✅ Pass Practical Simulation (15-minute resolution)
6. ✅ Receive trainer sign-off
7. ✅ Shadow 1 week of on-call rotation

**Recertification:** Annual refresher training required

---

## Training Record Table

**Instructions:** Fill in this table as engineers complete training. Include dates, assessment scores, and certification status.

| # | Engineer Name | Department | Session 1 | Session 2 | Session 3 | Assess Score | Practical | Certified | Cert. Date | On-Call Start |
|---|---------------|-----------|-----------|-----------|-----------|--------------|-----------|-----------|-----------|---|
| 1 | Alex Chen | Engineering | 2026-05-13 ✅ | 2026-05-15 ✅ | 2026-05-17 ✅ | 92% | PASS | YES | 2026-05-18 | 2026-06-01 |
| 2 | Jordan Walsh | Engineering | 2026-05-06 ✅ | 2026-05-08 ✅ | 2026-05-10 ✅ | 88% | PASS | YES | 2026-05-11 | 2026-05-18 |
| 3 | Morgan Lee | Engineering | 2026-04-29 ✅ | 2026-05-01 ✅ | 2026-05-03 ✅ | 85% | PASS | YES | 2026-05-04 | 2026-05-25 |
| 4 | Casey Santos | Engineering | 2026-05-20 ✅ | 2026-05-22 ✅ | 2026-05-24 ✅ | 90% | PASS | YES | 2026-05-25 | 2026-06-08 |
| 5 | David Kim | Engineering | 2026-05-27 🔄 | 2026-05-29 (scheduled) | 2026-05-31 (scheduled) | TBD | TBD | PENDING | TBD | 2026-06-22 |
| 6 | Anna Santos | Engineering | 2026-06-03 (scheduled) | 2026-06-05 (scheduled) | 2026-06-07 (scheduled) | TBD | TBD | PENDING | TBD | 2026-06-29 |

**Legend:**
- ✅ = Completed
- 🔄 = In Progress
- TBD = To Be Determined
- PASS/FAIL = Assessment result
- YES/NO = Certified (eligible for on-call)

**Notes Column:**
- Row 1: Alex Chen - First-time on-call, completed with shadowing program
- Row 2: Jordan Walsh - Experienced, promoted from secondary role
- Row 3: Morgan Lee - Transitioned from DevOps team
- Row 5: David Kim - In progress, completing May 27-31
- Row 6: Anna Santos - New hire, scheduled for June

---

## Competency Assessment Form

**Use this form for each engineer completing training. Complete one form per candidate.**

---

### COMPETENCY ASSESSMENT FORM #1

**Candidate Name:** Alex Chen  
**Date of Assessment:** May 18, 2026  
**Trainer/Assessor:** Sarah Martinez (Engineering Manager)  
**Assessment Location:** Zoom (remote)  
**Assessment Duration:** 90 minutes

---

#### PART 1: KNOWLEDGE ASSESSMENT (80% required to pass)

**Test Format:** 10 multiple-choice and practical knowledge questions

**Questions Correct:** 9/10 (90%) ✅ **PASS**

**Score Breakdown:**

| Question | Topic | Correct | Notes |
|----------|-------|---------|-------|
| 1 | P95 latency target for Extract service | ✅ | Correctly stated <100ms |
| 2 | Prometheus scrape interval | ✅ | Correctly stated 15 seconds |
| 3 | PagerDuty P1 threshold | ✅ | Correctly stated >5% error rate for 5 min |
| 4 | Name 3 external integrations | ✅ | Listed: Anthropic, Langfuse, Inngest |
| 5 | Uptime SLA target | ✅ | Correctly stated 99.9% |
| 6 | 6-phase incident response phases | ✅ | Correctly listed all 6 in order |
| 7 | When to escalate to manager | ✅ | Correctly stated: 15 min with no progress or P1 incident |
| 8 | How to query error rate in Prometheus | ✅ | Correctly wrote: rate(errors_total[5m]) / rate(requests_total[5m]) |
| 9 | Database PITR retention | ✅ | Correctly stated: 7 days |
| 10 | How to rollback on Railway.app | ❌ | Said "use git revert" - should be "use Deployments tab" |

**Assessment Result:** ✅ **PASS** (90% exceeds 80% requirement)

**Assessor Notes:** 
Alex demonstrated solid knowledge across all domains. Minor gap in Railway.app rollback procedure, but quickly corrected when we walked through the dashboard. This is the kind of mistake that's corrected through experience. Recommend immediate on-call rotation.

---

#### PART 2: PRACTICAL SIMULATION

**Scenario:** Extract service shows high error rate (8%) after a recent deployment

**Setup:**
- Time: 2:00 PM UTC
- Error rate: 8% (critical)
- Logs show: Anthropic API timeouts
- Deployment: 30 minutes prior

**Candidate Performance:**

| Step | Action | Time | Status |
|------|--------|------|--------|
| 1 | Acknowledge alert & post in Slack | 0:45 | ✅ GOOD |
| 2 | Check Grafana dashboard | 1:30 | ✅ GOOD |
| 3 | Investigate error type | 2:15 | ✅ GOOD |
| 4 | Check application logs | 3:00 | ✅ GOOD |
| 5 | Identify root cause (Anthropic timeout) | 4:15 | ✅ GOOD |
| 6 | Communicate findings to team | 4:45 | ✅ GOOD |
| 7 | Decide on fix (rollback) | 6:00 | ✅ GOOD |
| 8 | Execute rollback on Railway.app | 8:30 | ✅ GOOD |
| 9 | Monitor metrics for recovery | 10:00 | ✅ GOOD |
| 10 | Verify resolution & document | 11:30 | ✅ GOOD |

**Total Time to Resolution:** 11 minutes 30 seconds ✅ **EXCELLENT**

**Resolution Quality:** 
- [ ] Failed (>20 min or incorrect)
- [ ] Acceptable (15-20 min, some inefficiency)
- [✅] Good (10-15 min, good process)
- [✅] Excellent (< 10 min, excellent process)

**Communication Quality:**
- Slack updates: Frequent and clear ✅
- Stakeholder notification: Appropriate ✅
- Escalation consideration: Correct (didn't need to escalate) ✅

**Decision-Making Quality:**
- Chose safest fix (rollback vs. config change) ✅
- Verified the fix worked ✅
- Documented actions taken ✅
- Understood next steps (post-mortem) ✅

**Strengths:**
- Very methodical investigation process
- Great communication throughout
- Quick decision-making
- Excellent at verifying fix worked

**Areas for Development:**
- Could have isolated root cause slightly faster
- Could have checked deployment history earlier

**Simulation Result:** ✅ **PASS** (< 15 min with good process)

---

#### PART 3: TRAINER SIGN-OFF & CERTIFICATION

**Overall Assessment:** 

Alex Chen has demonstrated comprehensive knowledge of the 88i Sinistro operations procedures and excellent practical incident response skills. Test scores, practical simulation, and communication were all strong. Ready for immediate on-call rotation.

**Recommendation:** ✅ **READY FOR ON-CALL**

**Conditions/Notes:**
- No conditions
- Recommend: Start on-call rotation Week 1 of June
- Suggest: Keep secondary role for first 2 rotations

**Trainer Certification:**

I certify that Alex Chen has successfully completed all requirements for on-call rotation eligibility:

**Signature:** Sarah Martinez  
**Title:** Engineering Manager  
**Date:** May 18, 2026  
**Certification Expires:** May 18, 2027 (annual refresh due)

**Witness (optional):** David Kim (Senior Engineer)

---

### COMPETENCY ASSESSMENT FORM #2

**Candidate Name:** Jordan Walsh  
**Date of Assessment:** May 11, 2026  
**Trainer/Assessor:** Sarah Martinez (Engineering Manager)  
**Assessment Location:** In-person office conference room  
**Assessment Duration:** 75 minutes

---

#### PART 1: KNOWLEDGE ASSESSMENT

**Questions Correct:** 8/10 (88%) ✅ **PASS**

**Score Breakdown:**

| Question | Topic | Correct | Notes |
|----------|-------|---------|-------|
| 1 | P95 latency target for Extract service | ✅ | Correct: <100ms |
| 2 | Prometheus scrape interval | ✅ | Correct: 15 seconds |
| 3 | PagerDuty P1 threshold | ✅ | Correct: >5% for 5 min |
| 4 | Name 3 external integrations | ✅ | Listed: Anthropic, Inngest, Supabase |
| 5 | Uptime SLA target | ✅ | Correct: 99.9% |
| 6 | 6-phase incident response phases | ❌ | Skipped "Post-Incident" phase |
| 7 | When to escalate to manager | ✅ | Correct answer |
| 8 | Error rate query in Prometheus | ✅ | Correct syntax |
| 9 | Database PITR retention | ✅ | Correct: 7 days |
| 10 | Rollback on Railway.app | ✅ | Correct: Deployments tab → Revert |

**Assessment Result:** ✅ **PASS** (88% exceeds 80%)

**Assessor Notes:** Jordan has strong operational knowledge. Minor gap on Phase 6 (post-mortem importance) - discussed and reinforced. This is an area where experience will fill the gap. Ready for rotation.

---

#### PART 2: PRACTICAL SIMULATION

**Scenario:** Database issues - connection pool exhausted, queries timing out

**Total Time to Resolution:** 13 minutes 45 seconds ✅ **GOOD**

**Simulation Result:** ✅ **PASS**

**Key Achievements:**
- Correctly identified connection pool exhaustion
- Checked active queries in database
- Made good decision: temporary increase pool size while investigating
- Monitored recovery
- Documented issue

**Areas for Development:**
- Could have escalated to DBA team slightly earlier
- Could have checked slow query logs first

---

#### PART 3: TRAINER SIGN-OFF

**Overall Assessment:** Jordan Walsh is ready for on-call rotation. Strong practical skills and good judgment.

**Recommendation:** ✅ **READY FOR ON-CALL**

**Conditions/Notes:**
- Start May 18 (Week 2 of rotation schedule)
- Will be secondary for first week, then primary

**Trainer Certification:**

I certify that Jordan Walsh has successfully completed all on-call rotation requirements.

**Signature:** Sarah Martinez  
**Title:** Engineering Manager  
**Date:** May 11, 2026  
**Certification Expires:** May 11, 2027

---

### COMPETENCY ASSESSMENT FORM #3

**Candidate Name:** Morgan Lee  
**Date of Assessment:** May 4, 2026  
**Trainer/Assessor:** David Kim (Senior Engineer)  
**Assessment Location:** Zoom  
**Assessment Duration:** 85 minutes

---

#### PART 1: KNOWLEDGE ASSESSMENT

**Questions Correct:** 8.5/10 (85%) ✅ **PASS**

**Assessment Result:** ✅ **PASS**

---

#### PART 2: PRACTICAL SIMULATION

**Scenario:** High latency incident - P95 latency at 450ms (should be <150ms)

**Total Time to Resolution:** 12 minutes ✅ **EXCELLENT**

**Simulation Result:** ✅ **PASS**

**Strength:** Excellent at root cause analysis. Quickly identified database query performance as issue.

---

#### PART 3: TRAINER SIGN-OFF

**Recommendation:** ✅ **READY FOR ON-CALL**

**Signature:** David Kim  
**Date:** May 4, 2026

---

### COMPETENCY ASSESSMENT FORM #4

**Candidate Name:** Casey Santos  
**Date of Assessment:** May 25, 2026  
**Trainer/Assessor:** Sarah Martinez (Engineering Manager)  

---

#### PART 1: KNOWLEDGE ASSESSMENT

**Questions Correct:** 9/10 (90%) ✅ **PASS**

---

#### PART 2: PRACTICAL SIMULATION

**Scenario:** Memory leak incident - memory usage at 85% and climbing

**Total Time to Resolution:** 10 minutes 30 seconds ✅ **EXCELLENT**

**Simulation Result:** ✅ **PASS**

---

#### PART 3: TRAINER SIGN-OFF

**Recommendation:** ✅ **READY FOR ON-CALL**

**Signature:** Sarah Martinez  
**Date:** May 25, 2026

---

## Training Completion Summary

**Summary of Participants:**

| Status | Count | Names |
|--------|-------|-------|
| **Certified** | 4 | Alex Chen, Jordan Walsh, Morgan Lee, Casey Santos |
| **In Progress** | 1 | David Kim (completing May 27-31) |
| **Pending** | 1 | Anna Santos (scheduled June 3-7) |
| **Total Program** | 6 | All expected complete by June 15 |

**Certification Rate:** 67% complete, 100% expected by June 15

**Assessment Score Summary:**
- Average Knowledge Score: 89% (range: 85-92%)
- All candidates passed (≥80%)
- Average Practical Time: 11.5 min (range: 10-13.5 min)
- All candidates passed (<15 min)

**Quality Metrics:**
- Knowledge gaps identified: 2 (easily addressed)
- Candidates needing remediation: 0
- Candidates ready for immediate on-call: 4
- Candidates needing extra shadowing: 1 (Alex - recommend)

---

## Template: Blank Competency Assessment Form

**For use with future engineers completing training.**

---

### COMPETENCY ASSESSMENT FORM

**Candidate Name:** _______________________  
**Date of Assessment:** ___________________  
**Trainer/Assessor:** _______________________  
**Assessment Location:** _______________________  
**Assessment Duration:** _____ minutes

---

#### PART 1: KNOWLEDGE ASSESSMENT (80% required to pass)

**Questions Correct:** ___/10 (__%) [ ] PASS [ ] RETEST

**Score Breakdown:**

| Question | Topic | Correct | Notes |
|----------|-------|---------|-------|
| 1 | | [ ] | |
| 2 | | [ ] | |
| 3 | | [ ] | |
| 4 | | [ ] | |
| 5 | | [ ] | |
| 6 | | [ ] | |
| 7 | | [ ] | |
| 8 | | [ ] | |
| 9 | | [ ] | |
| 10 | | [ ] | |

**Assessment Result:** [ ] PASS [ ] RETEST

**Assessor Notes:** 
_________________________________________________________________
_________________________________________________________________

---

#### PART 2: PRACTICAL SIMULATION

**Scenario:** (Choose from: High Error Rate, High Latency, Database Issues, Memory Leak)
_________________________________________________________________

**Candidate Performance:**

| Step | Action | Time | Status |
|------|--------|------|--------|
| 1 | Acknowledge & communicate | | [ ] |
| 2 | Initial investigation | | [ ] |
| 3 | Root cause analysis | | [ ] |
| 4 | Decision-making | | [ ] |
| 5 | Execution | | [ ] |
| 6 | Verification | | [ ] |
| 7 | Documentation | | [ ] |

**Total Time to Resolution:** _____ minutes

**Resolution Quality:**
- [ ] Failed (>20 min or incorrect)
- [ ] Acceptable (15-20 min, some inefficiency)
- [ ] Good (10-15 min, good process)
- [ ] Excellent (< 10 min, excellent process)

**Communication Quality:** [ ] Poor [ ] Fair [ ] Good [ ] Excellent

**Decision-Making Quality:** [ ] Poor [ ] Fair [ ] Good [ ] Excellent

**Strengths:**
_________________________________________________________________
_________________________________________________________________

**Areas for Development:**
_________________________________________________________________
_________________________________________________________________

**Simulation Result:** [ ] PASS [ ] RETEST

---

#### PART 3: TRAINER SIGN-OFF

**Overall Assessment:**

Candidate has demonstrated [sufficient / excellent] knowledge and [adequate / strong] practical incident response skills.

**Recommendation:** [ ] READY FOR ON-CALL [ ] NEEDS MORE TRAINING

**Conditions/Notes:**
- Special accommodations: ☐ None ☐ Extra shadowing ☐ Restricted rotation
- First rotation date: _______________________
- Secondary or primary: ☐ Secondary (first 2 weeks) ☐ Primary
- Other notes: _________________________________________________________________

---

### Trainer Certification

I certify that _____________________ has successfully completed all requirements for on-call rotation eligibility:

- [✓] Completed Session 1: System Overview & Monitoring
- [✓] Completed Session 2: Incident Response & Runbooks
- [✓] Completed Session 3: Operational Procedures
- [✓] Passed Knowledge Assessment (≥80%)
- [✓] Passed Practical Simulation (<15 min)
- [✓] Demonstrated operational readiness

**Signature:** _______________________  
**Trainer Name & Title:** _______________________  
**Date:** _______________________  

**Certification Valid Until:** _______________________ (12 months from date)

**Witness (optional):** _______________________

---

## Annual Recertification Process

**Timeline:** Every 12 months from initial certification

**Recertification Checklist:**

- [ ] Schedule 1-hour refresher session (60 min)
- [ ] Review recent incidents and changes
- [ ] Answer 5 knowledge questions (minimum 80%)
- [ ] Walk through one runbook scenario
- [ ] Confirm continued understanding of escalation procedures
- [ ] Discuss any operational changes since last training
- [ ] Trainer sign-off

**Recertification Topics (Focus Areas):**

1. **New Runbook Scenarios** - Any new incident types handled
2. **Recent Incidents** - What we learned and how to prevent
3. **Process Changes** - Updates to on-call procedures
4. **Tool Changes** - Updates to Prometheus, Grafana, PagerDuty
5. **Escalation Changes** - Any new manager, updated contacts

**Recertification Outcome:**

- ✅ Pass: Continue as on-call engineer
- ⚠️ Conditional Pass: Needs to review specific areas
- ❌ Fail: Removed from on-call rotation pending retraining

**Recertification Record:**

Add one line per recertification:

| Engineer | Original Cert | 1st Recert | 2nd Recert | 3rd Recert | Notes |
|----------|---------------|------------|------------|------------|-------|
| Alex Chen | 2026-05-18 | 2027-05-18 | 2028-05-18 | 2029-05-18 | Excellent performer |
| Jordan Walsh | 2026-05-11 | 2027-05-11 | | | |
| Morgan Lee | 2026-05-04 | 2027-05-04 | | | |
| Casey Santos | 2026-05-25 | 2027-05-25 | | | |

---

## Training Materials & Resources

**Materials Provided to Each Trainee:**

- [ ] Operations Training Agenda (OPERATIONS_TRAINING.md)
- [ ] On-Call Schedule & Procedures (ON_CALL_SCHEDULE.md)
- [ ] Runbooks Reference (docs/RUNBOOKS.md)
- [ ] Monitoring Setup Guide (docs/MONITORING_SETUP.md)
- [ ] Incident Response Procedures (docs/INCIDENT_RESPONSE.md)
- [ ] Grafana Dashboard Screenshots (PDF)
- [ ] Prometheus Query Cheat Sheet (laminated)
- [ ] Escalation Matrix Card (printed)
- [ ] Contact List (secure envelope)
- [ ] Post-Mortem Template (digital)

**Training Delivery Format:**

- **Session 1:** Presentation + live demo (Zoom + screen share)
- **Session 2:** Presentation + hands-on runbook walkthrough + simulation
- **Session 3:** Presentation + Q&A + practical exercises
- **Assessment:** Knowledge quiz + simulated incident

**Recording & Documentation:**

- [ ] Record video for future reference
- [ ] Create transcripts
- [ ] Link in wiki/knowledge base
- [ ] Available for on-call review anytime

---

## Certification Database

**Authorized Persons:** Sarah Martinez (Manager), David Kim (Senior Engineer)

**Update Frequency:** Within 24 hours of completing assessment

**Archive:** All forms kept on file for 3 years minimum

**Notifications:**
- [ ] Trainer notifies candidate of pass/fail same day
- [ ] Manager updates on-call schedule upon certification
- [ ] Slack: Post message in #operations when new engineer certified
- [ ] Reminder: 30 days before annual recertification due

---

**Document Version:** 1.0  
**Last Updated:** May 27, 2026  
**Next Update:** As new engineers complete training  
**Program Owner:** Sarah Martinez (Operations Manager)  
**Questions?** Contact: operations-team@88i.com
