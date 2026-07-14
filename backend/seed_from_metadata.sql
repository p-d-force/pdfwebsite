-- Generated from /cases/*/*/metadata.json
-- Non-deployment local seed for MySQL schema

-- Districts
INSERT INTO districts (district_code, district_name, location, status, notes) VALUES
  ('ATTLEBORO', 'Attleboro Public Schools', 'Attleboro, MA', 'active', NULL),
  ('FALLRIVER', 'Fall River Public Schools', 'Fall River, MA', 'active', NULL)
ON DUPLICATE KEY UPDATE district_name = VALUES(district_name), location = VALUES(location);

-- Cases
INSERT INTO cases (case_code, district_id, title, case_type, status, stage, subject, filed_date, next_deadline, next_deadline_description, recurrence_notes)
SELECT 'ATTLEBORO-PRR-002', d.id, 'Recordings, Transcripts, Minutes, Materials, Executive Session Releasable Records, and Financials', 'Public Records Request', 'open', 'Awaiting district production', 'Recordings, Transcripts, Minutes, Materials, Executive Session Releasable Records, and Financials', '2026-01-31', '2026-04-02', 'District portal/link production expected following active records tracking', NULL
FROM districts d WHERE d.district_code = 'ATTLEBORO'
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  case_type = VALUES(case_type),
  status = VALUES(status),
  stage = VALUES(stage),
  subject = VALUES(subject),
  filed_date = VALUES(filed_date),
  next_deadline = VALUES(next_deadline),
  next_deadline_description = VALUES(next_deadline_description),
  recurrence_notes = VALUES(recurrence_notes);
INSERT INTO cases (case_code, district_id, title, case_type, status, stage, subject, filed_date, next_deadline, next_deadline_description, recurrence_notes)
SELECT 'SPR26-0842', d.id, 'Professional Development Records', 'Public Records Request', 'open', 'Post-SPR Determination', 'Professional Development Records', '2026-02-18', '2026-04-02', 'District must provide response and records (10 business days from 03/19/2026 SPR determination)', 'Pattern of non-response documented - district has failed to respond within statutory timeline requiring escalation'
FROM districts d WHERE d.district_code = 'ATTLEBORO'
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  case_type = VALUES(case_type),
  status = VALUES(status),
  stage = VALUES(stage),
  subject = VALUES(subject),
  filed_date = VALUES(filed_date),
  next_deadline = VALUES(next_deadline),
  next_deadline_description = VALUES(next_deadline_description),
  recurrence_notes = VALUES(recurrence_notes);
INSERT INTO cases (case_code, district_id, title, case_type, status, stage, subject, filed_date, next_deadline, next_deadline_description, recurrence_notes)
SELECT 'FALLRIVER-PRR-001', d.id, 'Hiring Records for School Adjustment Counselor Position at Silvia Elementary', 'Public Records Request', 'open', 'Clarification in Progress', 'Hiring Records for School Adjustment Counselor Position at Silvia Elementary', '2026-03-05', '2026-03-20', 'District response expected after clarification sequence', NULL
FROM districts d WHERE d.district_code = 'FALLRIVER'
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  case_type = VALUES(case_type),
  status = VALUES(status),
  stage = VALUES(stage),
  subject = VALUES(subject),
  filed_date = VALUES(filed_date),
  next_deadline = VALUES(next_deadline),
  next_deadline_description = VALUES(next_deadline_description),
  recurrence_notes = VALUES(recurrence_notes);
INSERT INTO cases (case_code, district_id, title, case_type, status, stage, subject, filed_date, next_deadline, next_deadline_description, recurrence_notes)
SELECT 'FALLRIVER-PRR-002', d.id, 'Silvia Elementary Incident, Restraint, Staffing, and Safety Records', 'Public Records Request', 'open', 'Acknowledged', 'Silvia Elementary Incident, Restraint, Staffing, and Safety Records', '2026-03-06', '2026-03-20', 'Initial records response timeline after district acknowledgement', NULL
FROM districts d WHERE d.district_code = 'FALLRIVER'
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  case_type = VALUES(case_type),
  status = VALUES(status),
  stage = VALUES(stage),
  subject = VALUES(subject),
  filed_date = VALUES(filed_date),
  next_deadline = VALUES(next_deadline),
  next_deadline_description = VALUES(next_deadline_description),
  recurrence_notes = VALUES(recurrence_notes);
INSERT INTO cases (case_code, district_id, title, case_type, status, stage, subject, filed_date, next_deadline, next_deadline_description, recurrence_notes)
SELECT 'PRS-15514', d.id, 'DESE PRS 15514 - Request for Local Response', 'DESE PRS Complaint', 'open', 'Request for Local Response Issued', 'DESE PRS 15514 - Request for Local Response', '2026-03-19', '2026-04-07', 'District local response due to DESE and complainant supplemental submission deadline', NULL
FROM districts d WHERE d.district_code = 'FALLRIVER'
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  case_type = VALUES(case_type),
  status = VALUES(status),
  stage = VALUES(stage),
  subject = VALUES(subject),
  filed_date = VALUES(filed_date),
  next_deadline = VALUES(next_deadline),
  next_deadline_description = VALUES(next_deadline_description),
  recurrence_notes = VALUES(recurrence_notes);

-- Events
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-01-31', 'Filed', 'Broad PRR Submitted', 'Comprehensive request submitted for recordings, transcripts, meeting materials, releasable executive session records, and FY2022-present financial records.', NULL, 1
FROM cases c WHERE c.case_code = 'ATTLEBORO-PRR-002';
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-03-19', 'Production', 'Audio Archive Logged', 'Responsive meeting audio files were organized and indexed for public archive access pending full district delivery package.', NULL, 2
FROM cases c WHERE c.case_code = 'ATTLEBORO-PRR-002';
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-02-18', 'Filed', 'PRR Submitted', 'Professional Development Records request filed via Massachusetts PRR Form SPR26_0842. Seeking records related to [teacher name]''s professional development activities.', NULL, 1
FROM cases c WHERE c.case_code = 'SPR26-0842';
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-03-03', 'Appeal', 'Appeal Filed - Excessive Fee (C24-0260)', 'Filed appeal with Supervisor of Public Records regarding excessive fee estimate. District''s fee request was unreasonable and lacked proper documentation.', 'completed', 2
FROM cases c WHERE c.case_code = 'SPR26-0842';
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-03-19', 'Determination', 'SPR Determination - Response Ordered', 'Supervisor of Public Records issues determination ordering district to provide response and produce records.', 'completed', 3
FROM cases c WHERE c.case_code = 'SPR26-0842';
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-03-09', 'Appeal', 'Appeal Filed - Failure to Respond (C24-0713)', 'Second appeal filed for district''s failure to respond within statutory timeline. Documented pattern of non-compliance with Massachusetts Public Records Law.', 'completed', 4
FROM cases c WHERE c.case_code = 'SPR26-0842';
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-03-19', 'Correspondence', 'District Response Letter Received', 'Records Access Officer provided district response to narrowed scope request.', 'completed', 5
FROM cases c WHERE c.case_code = 'SPR26-0842';
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-03-19', 'Production', 'PD Database Export Produced', 'District provided spreadsheet export with section, instructor, targeted demographics, and class schedule fields for professional development sessions.', 'completed', 6
FROM cases c WHERE c.case_code = 'SPR26-0842';
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-03-05', 'Filed', 'Public Records Request Submitted', 'Initial request submitted regarding Andrea Souza hiring records for Silvia Elementary.', NULL, 1
FROM cases c WHERE c.case_code = 'FALLRIVER-PRR-001';
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-03-18', 'Correspondence', 'District Requests Clarification', 'District requested clarification for custodians and timeframe for item #6 communications.', NULL, 2
FROM cases c WHERE c.case_code = 'FALLRIVER-PRR-001';
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-03-19', 'Correspondence', 'Clarification Provided', 'Requester narrowed/clarified administrator and administrative employee scope with specific timeframe adjustment.', NULL, 3
FROM cases c WHERE c.case_code = 'FALLRIVER-PRR-001';
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-03-06', 'Filed', 'Public Records Request Submitted', 'Comprehensive request filed for incident, restraint, staffing, and communications records related to Silvia Elementary.', NULL, 1
FROM cases c WHERE c.case_code = 'FALLRIVER-PRR-002';
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-03-18', 'Correspondence', 'District Acknowledgement Received', 'District confirmed request receipt.', NULL, 2
FROM cases c WHERE c.case_code = 'FALLRIVER-PRR-002';
INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)
SELECT c.id, '2026-03-19', 'Determination', 'DESE Request for Local Response Issued', 'DESE PRS issued local response request with an April 7, 2026 deadline for district response and complainant supplemental submissions.', NULL, 1
FROM cases c WHERE c.case_code = 'PRS-15514';

-- Timeline documents
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'correspondence', '2026-01-31_Correspondence_ATTLEBORO-PRR-002_Broad_Meeting_Records_Request.eml', 'cases/ATTLEBORO/ATTLEBORO-PRR-002/correspondence/2026-01-31_Correspondence_ATTLEBORO-PRR-002_Broad_Meeting_Records_Request.eml', 'eml', '2026-01-31', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'ATTLEBORO-PRR-002' AND e.sort_order = 1
  AND e.title = 'Broad PRR Submitted';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'attachment', '2026-03-19_Attachment_ATTLEBORO-PRR-002_Audio_Manifest.txt', 'cases/ATTLEBORO/ATTLEBORO-PRR-002/attachments/2026-03-19_Attachment_ATTLEBORO-PRR-002_Audio_Manifest.txt', 'txt', '2026-03-19', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'ATTLEBORO-PRR-002' AND e.sort_order = 2
  AND e.title = 'Audio Archive Logged';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'document', 'recordings_index.json', 'cases/ATTLEBORO/ATTLEBORO-PRR-002/recordings_index.json', 'json', '2026-03-19', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'ATTLEBORO-PRR-002' AND e.sort_order = 2
  AND e.title = 'Audio Archive Logged';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'prr', '2026-02-18_PRR_SPR26-0842_PD_Records_Request.pdf', 'cases/ATTLEBORO/SPR26-0842/original-request/2026-02-18_PRR_SPR26-0842_PD_Records_Request.pdf', 'pdf', '2026-02-18', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'SPR26-0842' AND e.sort_order = 1
  AND e.title = 'PRR Submitted';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'appeal', '2026-03-03_Appeal_C24-0260_Excessive_Fee.pdf', 'cases/ATTLEBORO/SPR26-0842/appeals/2026-03-03_Appeal_C24-0260_Excessive_Fee.pdf', 'pdf', '2026-03-03', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'SPR26-0842' AND e.sort_order = 2
  AND e.title = 'Appeal Filed - Excessive Fee (C24-0260)';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'determination', '2026-03-19_SPR_Determination_SPR26-0842.pdf', 'cases/ATTLEBORO/SPR26-0842/determinations/2026-03-19_SPR_Determination_SPR26-0842.pdf', 'pdf', '2026-03-19', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'SPR26-0842' AND e.sort_order = 3
  AND e.title = 'SPR Determination - Response Ordered';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'correspondence', '2026-03-19_EmailNotice_SPR26-0842_Determination.pdf', 'cases/ATTLEBORO/SPR26-0842/correspondence/2026-03-19_EmailNotice_SPR26-0842_Determination.pdf', 'pdf', '2026-03-19', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'SPR26-0842' AND e.sort_order = 3
  AND e.title = 'SPR Determination - Response Ordered';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'appeal', '2026-03-09_Appeal_C24-0713_Failure_to_Respond.pdf', 'cases/ATTLEBORO/SPR26-0842/appeals/2026-03-09_Appeal_C24-0713_Failure_to_Respond.pdf', 'pdf', '2026-03-09', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'SPR26-0842' AND e.sort_order = 4
  AND e.title = 'Appeal Filed - Failure to Respond (C24-0713)';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'appeal', '2026-03-09_Appeal_C24-0713_Failure_to_Respond.eml', 'cases/ATTLEBORO/SPR26-0842/appeals/2026-03-09_Appeal_C24-0713_Failure_to_Respond.eml', 'eml', '2026-03-09', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'SPR26-0842' AND e.sort_order = 4
  AND e.title = 'Appeal Filed - Failure to Respond (C24-0713)';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'correspondence', '2026-03-19_Correspondence_SPR26-0842_District_Response_to_Narrowed_Scope.eml', 'cases/ATTLEBORO/SPR26-0842/correspondence/2026-03-19_Correspondence_SPR26-0842_District_Response_to_Narrowed_Scope.eml', 'eml', '2026-03-19', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'SPR26-0842' AND e.sort_order = 5
  AND e.title = 'District Response Letter Received';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'correspondence', '2026-03-19_Correspondence_SPR26-0842_District_Response_Letter.pdf', 'cases/ATTLEBORO/SPR26-0842/correspondence/2026-03-19_Correspondence_SPR26-0842_District_Response_Letter.pdf', 'pdf', '2026-03-19', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'SPR26-0842' AND e.sort_order = 5
  AND e.title = 'District Response Letter Received';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'attachment', '2026-03-19_Attachment_SPR26-0842_PD_Database_Export.xlsx', 'cases/ATTLEBORO/SPR26-0842/attachments/2026-03-19_Attachment_SPR26-0842_PD_Database_Export.xlsx', 'xlsx', '2026-03-19', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'SPR26-0842' AND e.sort_order = 6
  AND e.title = 'PD Database Export Produced';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'correspondence', '2026-03-19_Correspondence_FALLRIVER-PRR-001_Hiring_Records_Clarification.eml', 'cases/FALLRIVER/FALLRIVER-PRR-001/correspondence/2026-03-19_Correspondence_FALLRIVER-PRR-001_Hiring_Records_Clarification.eml', 'eml', '2026-03-05', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'FALLRIVER-PRR-001' AND e.sort_order = 1
  AND e.title = 'Public Records Request Submitted';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'correspondence', '2026-03-19_Correspondence_FALLRIVER-PRR-001_Hiring_Records_Clarification.eml', 'cases/FALLRIVER/FALLRIVER-PRR-001/correspondence/2026-03-19_Correspondence_FALLRIVER-PRR-001_Hiring_Records_Clarification.eml', 'eml', '2026-03-18', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'FALLRIVER-PRR-001' AND e.sort_order = 2
  AND e.title = 'District Requests Clarification';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'correspondence', '2026-03-19_Correspondence_FALLRIVER-PRR-001_Hiring_Records_Clarification.eml', 'cases/FALLRIVER/FALLRIVER-PRR-001/correspondence/2026-03-19_Correspondence_FALLRIVER-PRR-001_Hiring_Records_Clarification.eml', 'eml', '2026-03-19', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'FALLRIVER-PRR-001' AND e.sort_order = 3
  AND e.title = 'Clarification Provided';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'correspondence', '2026-03-19_Correspondence_FALLRIVER-PRR-002_Request_Acknowledgement.eml', 'cases/FALLRIVER/FALLRIVER-PRR-002/correspondence/2026-03-19_Correspondence_FALLRIVER-PRR-002_Request_Acknowledgement.eml', 'eml', '2026-03-06', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'FALLRIVER-PRR-002' AND e.sort_order = 1
  AND e.title = 'Public Records Request Submitted';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'correspondence', '2026-03-19_Correspondence_FALLRIVER-PRR-002_Request_Acknowledgement.eml', 'cases/FALLRIVER/FALLRIVER-PRR-002/correspondence/2026-03-19_Correspondence_FALLRIVER-PRR-002_Request_Acknowledgement.eml', 'eml', '2026-03-18', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'FALLRIVER-PRR-002' AND e.sort_order = 2
  AND e.title = 'District Acknowledgement Received';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'correspondence', '2026-03-19_Correspondence_PRS-15514_Request_for_Local_Response.eml', 'cases/FALLRIVER/PRS-15514/correspondence/2026-03-19_Correspondence_PRS-15514_Request_for_Local_Response.eml', 'eml', '2026-03-19', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'PRS-15514' AND e.sort_order = 1
  AND e.title = 'DESE Request for Local Response Issued';
INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)
SELECT c.id, e.id, 'determination', '2026-03-19_Determination_PRS-15514_Request_for_Local_Response.pdf', 'cases/FALLRIVER/PRS-15514/determinations/2026-03-19_Determination_PRS-15514_Request_for_Local_Response.pdf', 'pdf', '2026-03-19', 0
FROM cases c
JOIN case_events e ON e.case_id = c.id
WHERE c.case_code = 'PRS-15514' AND e.sort_order = 1
  AND e.title = 'DESE Request for Local Response Issued';

-- Related case links
INSERT IGNORE INTO case_links (from_case_id, to_case_id, link_type, notes)
SELECT src.id, dst.id, 'related', NULL
FROM cases src
JOIN cases dst
  ON src.case_code = 'SPR26-0842' AND dst.case_code = 'ATTLEBORO-PRR-002';
