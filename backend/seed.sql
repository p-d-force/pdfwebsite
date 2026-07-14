-- Minimal local seed data for current Attleboro cases
-- Intended for local phpMyAdmin import only (no deployment step)

INSERT INTO districts (district_code, district_name, location, status, notes)
VALUES
  ('ATTLEBORO', 'Attleboro Public Schools', 'Attleboro, MA', 'active', 'Records and accountability tracking');

INSERT INTO cases (
  case_code,
  district_id,
  title,
  case_type,
  status,
  stage,
  subject,
  filed_date,
  next_deadline,
  next_deadline_description,
  recurrence_notes
)
SELECT
  'SPR26-0842',
  d.id,
  'Professional Development Records Request',
  'Public Records Request',
  'open',
  'Response Package Review',
  'Professional Development Records',
  '2026-02-18',
  '2026-04-02',
  'District must provide response and records',
  'Pattern of delayed or incomplete records response tracked for recurrence'
FROM districts d WHERE d.district_code = 'ATTLEBORO';

INSERT INTO cases (
  case_code,
  district_id,
  title,
  case_type,
  status,
  stage,
  subject,
  filed_date,
  next_deadline,
  next_deadline_description,
  recurrence_notes
)
SELECT
  'ATTLEBORO-PRR-002',
  d.id,
  'Meetings, Recordings, and Financials Archive Request',
  'Public Records Request',
  'open',
  'Awaiting district production',
  'Recordings, transcripts, minutes, executive session releasable portions, and financials',
  '2026-01-31',
  '2026-04-02',
  'District portal/link production expected for responsive materials',
  'Archive-wide monitoring of phased release patterns'
FROM districts d WHERE d.district_code = 'ATTLEBORO';
