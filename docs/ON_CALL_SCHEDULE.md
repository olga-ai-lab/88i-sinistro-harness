# On-Call Rotation Schedule

**Program:** 88i Sinistro Agent Operations  
**Effective Date:** June 1, 2026  
**Update Frequency:** Monthly  
**Coverage Model:** 24/7 with primary, secondary, and escalation  
**Handoff Schedule:** Every Monday 9:00 AM UTC  
**Contact:** operations-team@88i.com | Slack: #operations-schedule

---

## Overview

This document defines the on-call rotation for the 88i Sinistro Agent production system. The rotation ensures 24/7 coverage with clear escalation paths and regular handoff procedures.

**Key Principles:**

- **24/7 Coverage:** One engineer always responsible for incidents
- **Predictable Schedule:** Weekly rotations on Monday 9 AM UTC
- **Clear Escalation:** Primary → Secondary → Manager
- **Regular Handoff:** Structured 30-minute transition each Monday
- **Knowledge Sharing:** Outgoing on-call documents learnings
- **Fair Distribution:** Equal burden across team
- **Compensation:** Hazard pay + flexible hours during on-call week

---

## Rotation Schedule (Example: June 2026)

### Week 1 (June 1-7, 2026)

| Role | Engineer | Contact | Available |
|------|----------|---------|-----------|
| **Primary On-Call** | Alex Chen | @alex.chen | 24/7 all week |
| **Secondary On-Call** | Jordan Walsh | @jordan.walsh | Business hours + escalation |
| **Escalation Manager** | Sarah Martinez | @sarah.martinez | P1 issues only |
| **Backup Escalation** | David Kim | @david.kim | If Sarah unavailable |

**Schedule:**
- Monday 9 AM: Alex takes primary from previous rotation
- Tuesday-Sunday 24/7: Alex responds to all alerts
- Monday 9 AM (Week 2): Handoff to next engineer

**Contact Methods:**
- Primary: PagerDuty page (alert) + Slack direct message
- Secondary: Called after 5 minutes if primary doesn't respond
- Manager: Paged for P1 incidents

**Known Issues This Week:**
- Database backups may cause brief latency spike 2-4 AM Tuesday (expected)
- Scheduled deployment Friday 8 PM UTC (Alex coordinating)
- One new junior engineer shadowing (Anna Santos)

---

### Week 2 (June 8-14, 2026)

| Role | Engineer | Contact | Available |
|------|----------|---------|-----------|
| **Primary On-Call** | Jordan Walsh | @jordan.walsh | 24/7 all week |
| **Secondary On-Call** | Morgan Lee | @morgan.lee | Business hours + escalation |
| **Escalation Manager** | Sarah Martinez | @sarah.martinez | P1 issues only |
| **Backup Escalation** | David Kim | @david.kim | If Sarah unavailable |

**Schedule:**
- Monday 9 AM: Jordan takes primary from Alex
- Handoff meeting agenda:
  - Review last week's incidents (expect 2-3 minor)
  - Discuss scheduled deployment happening Friday
  - Verify Jordan has access to all tools
  - Confirm known issues documented
  - Review recent changes to production

**Known Issues This Week:**
- Anthropic API rate limit may trigger in US peak hours (mitigated by batch size reduction)
- Redis cache may have high eviction rate (monitor and consider resize)
- Two new alerts added to monitoring (review with Jordan)

---

### Week 3 (June 15-21, 2026)

| Role | Engineer | Contact | Available |
|------|----------|---------|-----------|
| **Primary On-Call** | Morgan Lee | @morgan.lee | 24/7 all week |
| **Secondary On-Call** | Casey Santos | @casey.santos | Business hours + escalation |
| **Escalation Manager** | Sarah Martinez | @sarah.martinez | P1 issues only |
| **Backup Escalation** | David Kim | @david.kim | If Sarah unavailable |

**Schedule:**
- Monday 9 AM: Morgan takes primary from Jordan
- Tuesday: Quarterly disaster recovery test (Morgan leading)
  - Database restore from backup
  - Application failover procedure
  - Expected duration: 2 hours during off-peak
  - Communicate to stakeholders in advance

**Known Issues This Week:**
- Planning major database schema change Friday evening (low-traffic window)
- Will need close monitoring during change window
- Morgan to have DBA team on standby

---

### Week 4 (June 22-28, 2026)

| Role | Engineer | Contact | Available |
|------|----------|---------|-----------|
| **Primary On-Call** | Casey Santos | @casey.santos | 24/7 all week |
| **Secondary On-Call** | Alex Chen | @alex.chen | Business hours + escalation |
| **Escalation Manager** | Sarah Martinez | @sarah.martinez | P1 issues only |
| **Backup Escalation** | David Kim | @david.kim | If Sarah unavailable |

**Schedule:**
- Monday 9 AM: Casey takes primary from Morgan
- Wednesday: Monthly post-launch review meeting
  - Review 30-day uptime and metrics
  - Discuss any recurring issues
  - Plan next month's improvements

**Known Issues This Week:**
- Normal operations expected
- Good time for catching up on post-mortem action items
- Prepare for monthly capability refresh training (July)

---

## On-Call Rotation Roles & Responsibilities

### Role 1: Primary On-Call Engineer

**Duration:** Full week (Monday 9 AM - Sunday 11:59 PM UTC + next Monday until 9 AM handoff)

**Responsibilities:**

| Responsibility | Details | SLA |
|---|---|---|
| **Alert Response** | Respond to all PagerDuty pages | Within 5 minutes |
| **Incident Investigation** | Determine root cause of alerts | First assessment within 10 min |
| **Status Communication** | Keep team informed via Slack | Update every 5 min (P1) or 15 min (P2) |
| **Incident Resolution** | Execute fix or escalate appropriately | Target: 15-30 min resolution |
| **Documentation** | Document all incidents and actions taken | Within 1 hour of resolution |
| **Escalation** | Know when to escalate to secondary/manager | After 10-15 min with no progress |
| **Handoff Notes** | Prepare comprehensive handoff for next on-call | Before Monday 9 AM handoff |
| **Tool Access Verification** | Ensure all systems accessible and working | Check on first day of rotation |
| **Knowledge Updates** | Update runbooks if procedures changed | As discovered during week |
| **Post-Incident Follow-up** | Schedule and lead post-mortems for major incidents | Within 24 hours of incident |

**Primary On-Call Should NOT:**

- ❌ Ignore alerts because they're inconvenient
- ❌ Assume secondary will handle it if they're overwhelmed
- ❌ Make major code changes during incidents (hotfixes only)
- ❌ Forget to document what they did
- ❌ Skip post-mortems
- ❌ Work more than 12-14 hours in a day (take breaks)

**Primary On-Call Should:**

- ✅ Keep phone accessible at all times
- ✅ Have backup internet connection
- ✅ Know escalation contacts by heart
- ✅ Update team every few minutes during major incident
- ✅ Ask for help when stuck
- ✅ Take notes on everything

**Compensation:**

- Base on-call pay (varies by company)
- Hazard bonus: 25% increase for on-call week
- Emergency callback: If called outside on-call week, time-and-a-half pay
- Flexible hours: Can adjust schedule for medical appointments, etc.
- Time off: Consider offering day off after intense on-call week

**Work-Life Balance:**

- On-call week: Expect 1-3 incidents (varies)
- Typical incident: 20-30 minutes to resolution
- Overnight incidents: Can impact sleep
- Recommendation: On-call weeks followed by less stressful week if possible

**First-Time On-Call:**

- Shadowing: Recommended to shadow experienced on-call engineer 1-2 weeks first
- Mentoring: Have experienced on-call available for questions (but primary makes decisions)
- Extra monitoring: More frequent check-ins with secondary/manager
- Confidence building: Start with simpler incidents

---

### Role 2: Secondary On-Call Engineer

**Duration:** Full week (Monday 9 AM - Sunday 11:59 PM UTC)

**Responsibilities:**

| Responsibility | Details | When |
|---|---|---|
| **Escalation Backup** | Available if primary doesn't respond | After 5 minutes of page |
| **Complex Issue Support** | Assist primary with difficult investigations | When requested by primary |
| **Business Hours Coverage** | Primary contact during 9-5 PM local time | Monday-Friday daytime |
| **Verification** | Second set of eyes on major decisions | During P1 incidents |
| **Documentation Review** | Review primary's incident documentation | Daily |
| **Issue Tracking** | Create tickets for follow-up items | During incidents |
| **Team Communication** | Assist with stakeholder updates | During major incidents |
| **Learning** | Observe primary's incident handling | Throughout week |

**Secondary On-Call Should:**

- ✅ Be responsive and engaged
- ✅ Learn from how primary handles incidents
- ✅ Help with tasks to reduce primary's load
- ✅ Speak up if you see something concerning
- ✅ Be ready to take over if primary unavailable

**Secondary On-Call Should NOT:**

- ❌ Take primary's role unless explicitly asked
- ❌ Override primary's decisions
- ❌ Disappear during business hours
- ❌ Hesitate to offer suggestions
- ❌ Let primary handle everything alone (especially for P1)

**Compensation:**

- Usually unpaid (part of regular duties)
- Or: Flat day-rate if significant escalations
- Benefit: Experience and learning for future primary rotation
- Recommendation: Should become primary every 4-6 weeks

---

### Role 3: Escalation Manager

**Duration:** On-call for P1 only (not every incident)

**Responsibilities:**

| Responsibility | Details | When |
|---|---|---|
| **P1 Escalation** | Page when P1 incident escalated | Triggered by PagerDuty rules |
| **Critical Decisions** | Approve major actions (rollbacks, etc.) | During P1 incidents |
| **Customer Communication** | Contact customers for P1 issues | If customer-facing incident |
| **Executive Updates** | Brief leadership on serious incidents | For major outages |
| **Backup Authority** | Take command if primary/secondary unavailable | Rare emergency situations |
| **Follow-up** | Ensure post-mortem happens | Within 24 hours of P1 |

**Escalation Manager is typically:**

- Engineering manager or director
- Most experienced ops engineer
- Person with authority to make big decisions
- Person with customer relationships
- Has strategic view, not just tactical

**Escalation Manager should NOT:**

- ❌ Try to debug technical issues (that's primary's job)
- ❌ Micromanage incident response
- ❌ Make decisions without consulting technical team
- ❌ Be hands-off (should be engaged but not controlling)

**When to Page Escalation Manager:**

- Error rate > 5% for > 5 minutes (P1)
- Service completely down (P1)
- Affecting customers, no quick fix (P1)
- Need to approve rollback or major action (P1)
- Need to contact customer or executive (P1)
- Primary uncertain about decision (escalate to ask advice)

---

## On-Call Responsibilities Table

### Summary Matrix

| Task | Primary | Secondary | Manager | Notes |
|------|---------|-----------|---------|-------|
| Respond to alerts | YES | Only if primary unavailable | No | Primary responsibility |
| Investigate incidents | YES | Assist if needed | No | Primary leads investigation |
| Make technical decisions | YES | Suggest | Approve for major changes | Primary decides, manager escalates |
| Update stakeholders | YES | Assist | For P1 incidents | Frequent updates (5 min intervals) |
| Execute runbooks | YES | Assist | Advise | Primary executes, secondary assists |
| Approve rollback | YES (for minor rollback) | Suggest | YES (for major rollback) | Manager decision for big changes |
| Escalate issues | YES (to secondary/manager) | YES (to manager) | As needed | Clear escalation path |
| Create tickets | YES | Help | No | For follow-up investigations |
| Schedule post-mortem | YES | Suggest | YES (for P1) | Primary leads, manager records |
| Update documentation | YES | Help | Suggest | Primary responsible, all contribute |
| Handoff to next | YES | Assist | Review | Primary writes detailed handoff |

---

## Handoff Procedure (Every Monday 9 AM UTC)

### Pre-Handoff (Friday-Sunday)

**Outgoing On-Call Engineer Actions (throughout the week):**

1. **Document incidents as they happen**
   - Create Slack thread for each incident
   - Include: Time, symptoms, root cause, resolution, duration
   - Link to any created tickets

2. **Keep handoff notes**
   - Maintain list of issues encountered
   - Note any flaky behavior
   - Document recent changes or deployments

3. **Prepare summary**
   - By Sunday evening, compile incident summary
   - Count incidents by severity: P1, P2, P3
   - Calculate average MTTR
   - Note worst incident

4. **Verify access**
   - Ensure incoming on-call has credentials
   - Grant any new access needed
   - Share secure passwords via LastPass or similar

### During Handoff (Monday 9 AM UTC)

**Duration:** 30 minutes

**Attendees:**
1. Outgoing on-call engineer (preparing to transition)
2. Incoming on-call engineer (taking over)
3. Team lead or manager (observing and ensuring accuracy)

**Handoff Meeting Agenda:**

**Time Allocation:**

```
9:00-9:05 AM: Opening & Last-Minute Issues (5 min)
├─ Outgoing reviews any new incidents from overnight
├─ Any critical context from last 12 hours
└─ Confirm incoming ready to take over

9:05-9:10 AM: Last Week's Incidents Summary (5 min)
├─ Total incidents: [#P1, #P2, #P3]
├─ Worst incident: [description, duration]
├─ Average MTTR: [time]
├─ Any patterns noticed: [summary]
└─ Post-mortem status: [any scheduled]

9:10-9:15 AM: Outstanding Issues (5 min)
├─ Any unresolved incidents: [list]
├─ Any known flaky components: [list]
├─ Any alerts that might be noisy: [list]
├─ Any expected high-load windows: [note]
└─ Any scheduled maintenance: [when]

9:15-9:20 AM: Tool Access & Verification (5 min)
├─ Incoming tests each tool access:
│  ├─ [ ] Grafana (load dashboard, can see metrics)
│  ├─ [ ] Prometheus (can run query)
│  ├─ [ ] PagerDuty (confirm on-call schedule shows correctly)
│  ├─ [ ] Railway.app dashboard (can view logs, deployment history)
│  ├─ [ ] Supabase dashboard (can view database)
│  ├─ [ ] SSH access to systems (if applicable)
│  └─ [ ] Slack access to all channels (#operations, etc.)
├─ If any access missing → Request immediately
└─ Confirm all accesses work before ending call

9:20-9:25 AM: Recent Changes & Deployments (5 min)
├─ Recent deployments (this week): [list]
├─ Database migrations (pending): [list]
├─ Configuration changes: [list]
├─ New alert rules (added): [list]
├─ Known issues with recent changes: [list]
└─ Recommended monitoring focus: [areas]

9:25-9:28 AM: Contact List & Escalation (3 min)
├─ Critical contacts (have phone numbers):
│  ├─ Escalation manager: [name, phone]
│  ├─ Database team lead: [name, phone]
│  ├─ Infrastructure lead: [name, phone]
│  ├─ Product on-call: [name, phone]
│  └─ Customer support manager: [phone]
├─ Verify all contacts are current
└─ Confirm incoming has written down numbers

9:28-9:30 AM: Closing & Confirmation (2 min)
├─ Outgoing: "Any final questions?"
├─ Incoming: Confirm ready to take over
├─ Manager: "Confirming transition complete?"
├─ Incoming: Takes primary role
└─ Outgoing: Officially off on-call
```

### Post-Handoff (Monday 9 AM onward)

**Incoming On-Call Engineer Actions (first day):**

1. **Test tool access immediately**
   - Don't assume everything works
   - Log in to each system
   - Run a test query in Prometheus
   - Verify PagerDuty shows you as on-call
   - Confirm Slack notifications working

2. **Review handoff notes**
   - Read all incident summaries
   - Check any open tickets
   - Understand known issues
   - Read recent deployment notes

3. **Check current system health**
   - Look at Grafana main dashboard
   - Verify all services showing healthy
   - Check error rate, latency, resource usage
   - Note if anything looks unusual

4. **Confirm monitoring is working**
   - Check that you receive Slack alerts
   - Verify PagerDuty page came through
   - Test by running a quick Prometheus query
   - Confirm mobile PagerDuty app working

5. **Post confirmation in Slack**
   ```
   ✅ ON-CALL ROTATION COMPLETE
   
   Outgoing: [Name] (great work last week!)
   Incoming: [Your name] (now primary until Mon 9 AM)
   
   Stats from last week:
   • Incidents: [#]
   • MTTR: [avg time]
   • Highest severity: [P1/P2/P3]
   
   Focus areas this week:
   • [Key known issues]
   
   Questions? Ask #operations or DM me
   ```

**Outgoing On-Call Engineer Actions (after transition):**

1. **Ensure knowledge transfer complete**
   - Ask incoming if they have questions
   - Be available for first few hours (if possible)
   - Follow-up: Check in after 24 hours
   - Offer to explain any complex situations

2. **Create post-mortem for major incidents (if not already done)**
   - Schedule meeting within 24 hours
   - Invite relevant engineers
   - Lead discussion and document findings

3. **Close out any follow-up items**
   - File tickets for improvements noted
   - Update runbooks if procedures changed
   - Share any learnings with team

4. **Take well-deserved break!**
   - You earned it
   - Relax before next rotation (maybe 4 weeks out)
   - Reflect on what went well

---

## Handoff Checklist (7-Item Verification)

**Use this checklist during every Monday 9 AM handoff to ensure nothing is missed:**

### Checklist Item 1: Incident Summary Reviewed

- [ ] Outgoing on-call provides written summary
- [ ] Summary includes:
  - [ ] Total incidents (count by severity: P1, P2, P3)
  - [ ] Incident descriptions (2-3 sentences each)
  - [ ] Root causes identified
  - [ ] MTTR for each incident
  - [ ] Whether post-mortem needed
- [ ] Team lead reviews summary for accuracy
- [ ] Incoming on-call understands current state

**Red Flag:** No summary provided = extend handoff, gather information

---

### Checklist Item 2: Outstanding Issues Discussed

- [ ] List of unresolved incidents: (check if any)
  - [ ] No open incidents, OR
  - [ ] Open incidents documented with context
- [ ] Known flaky components: (check if any)
  - [ ] No known issues, OR
  - [ ] Each issue documented: what, when it happens, mitigation
- [ ] Escalating problems: (check if any)
  - [ ] No escalating issues, OR
  - [ ] Each issue clearly documented and plan to address
- [ ] Incoming on-call understands what to monitor

**Example:**
```
Outstanding Issues:
1. Extract service occasionally times out (1x last week)
   - Happens when Anthropic API slow
   - Workaround: Reduce batch size
   - Needs long-term: Add retry logic
   
2. Database connections sometimes leak (needs investigation)
   - 3x last month
   - Usually resolves after restart
   - Monitor: db_connections_total metric
```

---

### Checklist Item 3: All Tool Access Verified & Working

**For each tool, incoming must:**
1. Log in successfully
2. Perform basic operation (e.g., view dashboard)
3. Confirm data is present and recent
4. Ask for help if any access missing

**Tools to verify:**

| Tool | Test Action | Expected Result | ✓ |
|------|-----------|-----------------|---|
| **Grafana** | Load main dashboard | Shows current metrics | [ ] |
| **Prometheus** | Run query: `rate(requests_total[5m])` | Returns number > 0 | [ ] |
| **PagerDuty** | Check schedule | Shows you as on-call | [ ] |
| **Railway.app** | View deployment history | Shows recent deployments | [ ] |
| **Supabase** | View database size | Returns size in bytes | [ ] |
| **Slack** | Verify #operations notifications | Can see channel | [ ] |

**If any access fails:**
- Immediately request access
- Don't take over until all access confirmed
- Document what was needed
- Follow up to grant access for next rotation

**Red Flag:** Missing access = do not transition, request immediately

---

### Checklist Item 4: Recent Changes & Deployments Reviewed

- [ ] List of recent deployments (last 7 days):
  - [ ] When deployed (date/time)
  - [ ] What changed (feature, bug fix, config)
  - [ ] Any issues noted since deployment
  - [ ] Any rollbacks needed

- [ ] Database schema changes or migrations:
  - [ ] Any pending migrations
  - [ ] Any backwards compatibility issues
  - [ ] Plan for rollout

- [ ] Configuration changes:
  - [ ] Any environment variable changes
  - [ ] Any infrastructure changes
  - [ ] Any monitoring changes

- [ ] Expected changes coming this week:
  - [ ] Scheduled deployments (when?)
  - [ ] Maintenance windows (when?)
  - [ ] Expected traffic spikes (when?)

**Example:**
```
Recent Changes:
- Deploy: May 25 @ 14:30 UTC (batch size optimization)
  Issue: Caused Anthropic timeouts
  Fix: Reduced batch size
  Status: Stable since fix
  
- Maintenance: Fri 8 PM UTC (new index on claims table)
  Expected downtime: < 1 minute
  Expected monitoring: Close watch on query latency
  Fallback: Rollback index creation
```

---

### Checklist Item 5: Contact Information Verified & Current

- [ ] Escalation Manager:
  - [ ] Name: _____________
  - [ ] Phone: _____________
  - [ ] Backup contact: _____________

- [ ] Database Team:
  - [ ] Lead name: _____________
  - [ ] Phone: _____________

- [ ] Infrastructure Team:
  - [ ] Lead name: _____________
  - [ ] Slack: _____________

- [ ] Customer Support:
  - [ ] Manager: _____________
  - [ ] Phone: _____________

- [ ] Product Team:
  - [ ] On-call point person: _____________
  - [ ] Slack: _____________

- [ ] Executive Escalation:
  - [ ] Director name: _____________
  - [ ] Phone: _____________

**Verification:**
- [ ] All contact info written down and verified
- [ ] Incoming has contact list (printed or secure storage)
- [ ] All phone numbers tested if possible
- [ ] Out-of-office contacts replaced with coverage

**Red Flag:** Missing or invalid contact = request immediately

---

### Checklist Item 6: Monitoring Health & Alerts Verified

- [ ] Prometheus is scraping metrics successfully
  - [ ] Check: All targets showing "UP"
  - [ ] Check: No "DOWN" targets
  - [ ] Run test query: Should complete in < 1 second

- [ ] Grafana dashboards loading properly
  - [ ] Check: Main dashboard displays current data
  - [ ] Check: Auto-refresh working (30-second intervals)
  - [ ] Check: All panels showing green/good status

- [ ] PagerDuty alerting configured correctly
  - [ ] Check: Integration enabled
  - [ ] Check: Incoming on-call listed as primary
  - [ ] Check: Escalation path configured
  - [ ] (Optional) Send test alert to confirm page delivery

- [ ] Slack notifications working
  - [ ] Check: #operations channel accessible
  - [ ] Check: Can see recent incident messages
  - [ ] Check: Desktop/mobile notifications enabled

**Example Test Alert (if available):**
- In PagerDuty, trigger test incident
- Confirm page sent within 30 seconds
- Confirm notification appears in Slack
- Acknowledge and resolve test incident
- Confirm this worked before transitioning

---

### Checklist Item 7: Knowledge Transfer & Incoming Readiness Confirmed

**Questions to ask Incoming On-Call:**

1. "What would you do if you got a P1 page right now?"
   - [ ] Should mention: ack alert, check Grafana, post in Slack
   - [ ] Should understand: basic incident response

2. "Where would you find the runbooks?"
   - [ ] Should say: docs/RUNBOOKS.md or link to it
   - [ ] Should know: how to navigate to right scenario

3. "Who would you escalate to for a critical decision?"
   - [ ] Should say: Escalation Manager [name]
   - [ ] Should have their contact info

4. "What should you do at the end of your on-call week?"
   - [ ] Should mention: prepare handoff summary, document incidents
   - [ ] Should understand: pass on knowledge to next engineer

5. "Do you feel ready to take over?"
   - [ ] Should express confidence (or ask for clarification)
   - [ ] Should understand: can ask for help during week

**Sign-Off:**

- [ ] Outgoing on-call: "I confirm this transition is complete"
- [ ] Incoming on-call: "I confirm I'm ready to take over"
- [ ] Manager/Lead: "I confirm this handoff was complete and correct"
- [ ] Time transition complete: ___:___ UTC

**Red Flag:** Incoming doesn't feel ready = extend handoff, provide more training/shadowing

---

## Special Handoff Situations

### Situation 1: On-Call Unavailable for Handoff

**If outgoing on-call can't attend Monday handoff:**

1. Schedule handoff earlier (Sunday evening)
2. Or: Manager conducts handoff with outgoing by email/Slack
3. Or: Previous on-call (week before) fills in details from notes
4. Ensure complete information transfer still happens
5. Document any information gaps

### Situation 2: Incoming On-Call Calls In Sick During Week

**If incoming on-call becomes unavailable (illness, emergency, etc.):**

1. Secondary takes over as primary immediately
2. Manager notifies escalation manager
3. If secondary also unavailable: Manager becomes primary
4. Post-pone incoming's rotation to following week (if same week sickness)
5. Ensure coverage is 24/7

### Situation 3: Major Incident During Handoff

**If P1 incident triggers during Monday 9 AM handoff meeting:**

1. Pause handoff immediately
2. Both on-calls (outgoing and incoming) respond to incident
3. Incoming can "shadow" handling while still transitioning
4. Complete handoff as soon as incident is stable
5. Document incident thoroughly

### Situation 4: New Hire or First-Time On-Call

**If incoming is new or first-time on-call:**

1. Extend handoff to 45 minutes (instead of 30)
2. Have manager or senior engineer assist
3. Go through each checklist item more carefully
4. Have incoming repeat back understanding
5. Plan for closer monitoring during first rotation
6. Provide extra support (don't hesitate to call incoming during week)

### Situation 5: Between-Rotation Gaps or Coverage Issues

**If there's no clear next on-call assigned:**

1. Manager must assign someone immediately
2. That person is now "incoming on-call" for handoff
3. Scheduled handoff still occurs Monday 9 AM
4. Document in #operations-schedule why original plan changed

---

## On-Call Schedule Expectations & Norms

### What Incoming On-Call Can Expect

**Incident Frequency:**
- Typical: 2-5 incidents per week
- Busy: 5-10 incidents
- Slow: 0-2 incidents
- **Pattern:** Weekday incidents more common than weekend

**Incident Types (Expected Distribution):**
- 70% P3 (low-severity, non-blocking) - Easy to fix
- 25% P2 (medium-severity) - Requires troubleshooting
- 5% P1 (critical, blocking) - Needs urgent response

**Time Commitment:**
- Alert response: Usually < 5 minutes per alert
- Investigation: 5-15 minutes for most incidents
- Resolution: 15-45 minutes (average 25 min)
- Typical total: 1-3 hours of active work per week
- Plus: Monitoring/vigilance (stay alert, but low energy)

**Sleep Impact:**
- Nighttime alerts: Happens occasionally
- PagerDuty app ensures you wake up
- Many on-call engineers sleep near phone
- Recommendation: Take it easy the next day if sleep interrupted
- Note: Can negotiate flexibility after late-night incident

### Work-Life Balance During On-Call Week

**Best Practices:**

1. **Stay nearby:**
   - Work from home if possible
   - Or: Stay within cell service range
   - Keep phone with good battery

2. **Plan activities carefully:**
   - Can still do hobbies/exercise (stay alert)
   - Avoid: Getting drunk, going to movies, sleeping through alerts
   - Perfect for: Local hangouts, reading, gaming, walks

3. **Rest when not dealing with incidents:**
   - Don't stress if no alerts
   - That's actually a good sign (system healthy)
   - Sleep normally, take breaks

4. **Communication is key:**
   - Tell friends/family you're on-call
   - They understand if you get called away
   - Set expectations: might need to step away

5. **Handoff after-hours incidents:**
   - If incident at 2 AM, you can take it easy next day
   - Flexible about starting work time
   - Or: Take day off if very late night incident
   - Talk to manager about balance

### What Happens If You Miss an Alert

**If you miss a page (didn't respond in 5 minutes):**

1. Secondary automatically paged after 5 minutes
2. You get a notification that secondary was paged
3. Respond immediately when you notice
4. Take over from secondary (apologize, thanks them)
5. Continue response

**If you miss multiple pages:**

1. Manager may call to check if you're okay
2. Discuss if on-call week is too stressful
3. Consider: Different time zone rotation? More shadowing?
4. Maybe not right time in life for on-call (temporary)
5. No judgment, but communication is important

**Prevention:**

- Set loud mobile alert for PagerDuty
- Multiple notification methods (app + SMS + email)
- Verify app working at start of week
- Don't silence notifications during on-call week
- Have backup charger nearby

---

## Rotation Calendar (Sample 3-Month View)

```
JUNE 2026

Week 1 (Jun 1-7):    Alex Chen (primary) | Jordan Walsh (secondary)
Week 2 (Jun 8-14):   Jordan Walsh        | Morgan Lee
Week 3 (Jun 15-21):  Morgan Lee          | Casey Santos  
Week 4 (Jun 22-28):  Casey Santos        | Alex Chen

JULY 2026

Week 1 (Jul 1-7):    Alex Chen           | Morgan Lee
Week 2 (Jul 8-14):   Morgan Lee          | Casey Santos
Week 3 (Jul 15-21):  Casey Santos        | Jordan Walsh
Week 4 (Jul 22-28):  Jordan Walsh        | Alex Chen

AUGUST 2026

Week 1 (Aug 1-7):    Morgan Lee          | Casey Santos
Week 2 (Aug 8-14):   Casey Santos        | Alex Chen
Week 3 (Aug 15-21):  Alex Chen           | Jordan Walsh
Week 4 (Aug 22-28):  Jordan Walsh        | Morgan Lee
Week 5 (Aug 29-31):  Morgan Lee          | Casey Santos
```

**Pattern:** Rotates among 5 engineers (Alex, Jordan, Morgan, Casey, David)
**Each engineer:** On-call about 1 week per month
**Distribution:** Fair, predictable, equal burden

---

## Escalation Matrix & Contact Tree

```
Customer Reports Issue
         ↓
   Primary On-Call
   (5 minute SLA)
    ↙         ↘
No Issue    Is Issue?
Found         ↓
             Can Fix?
           ↙        ↘
         YES          NO (escalate)
          ↓              ↓
       RESOLVE      Secondary On-Call
                   + Tech Investigation
                    (5 min SLA)
                         ↓
                      Can Fix?
                    ↙         ↘
                  YES           NO (escalate)
                   ↓              ↓
                RESOLVE    Escalation Manager
                          (decide action)
                              ↓
                        Can Fix?
                      ↙         ↘
                    YES           NO (escalate)
                     ↓              ↓
                  RESOLVE      Director
                            (executive decision)
                                 ↓
                             NOTIFY
                           CUSTOMER
```

**Response Times:**
- Primary: Within 5 minutes
- Secondary: Within 5 minutes of being paged
- Manager: Within 10 minutes of being paged
- Director: Within 15 minutes for P1

---

## Monthly Review & Feedback

**First Monday of Every Month: On-Call Retrospective**

**Attendees:** All on-call engineers, manager

**Agenda (30 minutes):**
1. Review incidents from past month (10 min)
2. Discuss any painful situations (10 min)
3. Identify improvements needed (5 min)
4. Plan changes for next month (5 min)

**Questions to Discuss:**
- Any recurring incident patterns?
- Any tools that weren't helpful?
- Any escalations that were mishandled?
- Any false alarms that wasted time?
- Any near-misses (things that could have been worse)?
- Any ideas for preventing incidents?

**Output:**
- Document lessons learned
- Update runbooks if needed
- Adjust escalation rules if needed
- Recognize great on-call work
- Plan improvements for next rotation

---

**Document Version:** 1.0  
**Last Updated:** May 27, 2026  
**Effective Date:** June 1, 2026  
**Next Review:** July 1, 2026  
**Maintained By:** Operations Manager
