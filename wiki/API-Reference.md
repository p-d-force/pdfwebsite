# API Reference

All endpoints return JSON. Base URL: `https://parentdataforce.com/api/`

## GET /api/data.php

District and restraint data queries.

| Param | Type | Description |
|---|---|---|
| `type` | string | `districts`, `restraint`, `trends`, `compare` |
| `district_code` | string | 8-digit DESE code |
| `school_year` | string | e.g. `2024` |

**Example:**
```
GET /api/data.php?type=restraint&district_code=00160000&school_year=2024
```

```json
{
  "data": [{
    "district_name": "Attleboro",
    "total_enrollment": 5942,
    "students_restrained": 42,
    "total_incidents": 187,
    "injuries_students": 3
  }]
}
```

## GET /api/cases.php

Active case data.

| Param | Type | Description |
|---|---|---|
| `case_number` | string | Case identifier |
| `district_code` | string | Filter by district |
| `status` | string | `active`, `resolved`, `pending` |

## GET /api/articles.php

Published articles and analysis. Supports `?type=` filter.

## GET /api/search.php

Full-text search.

| Param | Type | Description |
|---|---|---|
| `q` | string | Search query |
| `type` | string | `cases`, `articles`, `districts`, `all` |

## POST /api/submit.php

Anonymous tip submission.

| Field | Type | Description |
|---|---|---|
| `title` | string | Required |
| `body` | text | Submission content |
| `submitter_email` | string | Optional contact |
| `submission_type` | string | `tip`, `data`, `correction` |

## POST /api/subscribe.php

Email subscription.

| Field | Type | Description |
|---|---|---|
| `email` | string | Required |
