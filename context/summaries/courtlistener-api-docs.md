# CourtListener API Documentation (v4)

## Overview
CourtListener provides REST APIs for accessing legal data including case law, PACER data, oral arguments, judges, and financial disclosures. The API uses Django REST Framework and supports JSON, XML, and HTML serialization.

## Base URL
```
https://www.courtlistener.com/api/rest/v4/
```

## Authentication

### Methods Available
1. **Token Authentication** (Recommended for programmatic access)
   ```
   Authorization: Token YOUR_API_TOKEN
   ```

2. **Cookie/Session Authentication**
   - For browser-based access after logging into CourtListener

3. **HTTP Basic Authentication**
   ```
   curl --user "username:password" https://www.courtlistener.com/api/rest/v4/
   ```

### Rate Limits
- **Authenticated users**: 5,000 queries per hour
- **Unauthenticated users**: 100 queries per day (for experimentation)

## Core API Endpoints

### 1. Search API
**Endpoint**: `/api/rest/v4/search/`
- **Method**: GET
- **Purpose**: Search across millions of legal documents
- **Parameters**:
  - `q`: Search query
  - `type`: Filter by type (opinion, oral argument, etc.)
  - `court`: Filter by court ID
  - `filed_after`: Date filter (ISO-8601)
  - `filed_before`: Date filter (ISO-8601)
  - `cited_gt`: Minimum citation count
  - `cited_lt`: Maximum citation count

### 2. Dockets API
**Endpoint**: `/api/rest/v4/dockets/`
- **Method**: GET, POST
- **Purpose**: Access case docket information
- **Key Fields**:
  - `id`: Unique docket ID
  - `court`: Court ID
  - `case_name`: Name of the case
  - `docket_number`: Official docket number
  - `date_filed`: Filing date
  - `date_terminated`: Termination date
  - `nature_of_suit`: Type of lawsuit
  - `cause`: Cause of action

### 3. Opinion Clusters API
**Endpoint**: `/api/rest/v4/clusters/`
- **Method**: GET
- **Purpose**: Groups of related opinions in a case
- **Key Fields**:
  - `id`: Cluster ID
  - `docket`: Associated docket
  - `case_name`: Case name
  - `date_filed`: Filing date
  - `citation_count`: Number of times cited
  - `precedential_status`: Status of precedent
  - `sub_opinions`: List of associated opinions

### 4. Opinions API
**Endpoint**: `/api/rest/v4/opinions/`
- **Method**: GET
- **Purpose**: Individual court opinions/decisions
- **Key Fields**:
  - `id`: Opinion ID
  - `cluster`: Parent cluster
  - `author`: Judge who authored
  - `type`: Opinion type (lead, dissent, concurrence)
  - `html_with_citations`: HTML text with linked citations
  - `plain_text`: Plain text version
  - `xml_harvard`: Harvard CAP XML data
  - `opinions_cited`: List of cited opinions

### 5. Courts API
**Endpoint**: `/api/rest/v4/courts/`
- **Method**: GET, POST
- **Purpose**: Information about courts
- **Key Fields**:
  - `id`: Court identifier (e.g., "scotus", "nysd")
  - `full_name`: Full court name
  - `short_name`: Abbreviated name
  - `citation_string`: Citation abbreviation
  - `jurisdiction`: Type (F=Federal, S=State, etc.)
  - `start_date`: Court establishment date
  - `end_date`: Court closure date (if applicable)

### 6. People (Judges) API
**Endpoint**: `/api/rest/v4/people/`
- **Method**: GET
- **Purpose**: Judge biographical information
- **Key Fields**:
  - `id`: Person ID
  - `name_first`, `name_middle`, `name_last`
  - `date_dob`: Date of birth
  - `date_dod`: Date of death
  - `positions`: Judicial positions held
  - `educations`: Educational background
  - `political_affiliations`: Political party affiliations

### 7. Parties API
**Endpoint**: `/api/rest/v4/parties/`
- **Method**: GET
- **Purpose**: Party information in cases
- **Key Fields**:
  - `name`: Party name
  - `party_type`: Type of party
  - `docket`: Associated docket

### 8. Attorneys API
**Endpoint**: `/api/rest/v4/attorneys/`
- **Method**: GET
- **Purpose**: Attorney information
- **Key Fields**:
  - `name`: Attorney name
  - `contact_raw`: Contact information
  - `parties_represented`: Parties represented

### 9. Audio (Oral Arguments) API
**Endpoint**: `/api/rest/v4/audio/`
- **Method**: GET
- **Purpose**: Oral argument recordings
- **Key Fields**:
  - `id`: Audio ID
  - `docket`: Associated docket
  - `download_url`: Audio file URL
  - `duration`: Length in seconds
  - `local_path`: Server file path

### 10. RECAP APIs
Multiple endpoints for PACER data:
- `/api/rest/v4/recap/`: Upload RECAP documents
- `/api/rest/v4/recap-documents/`: RECAP document metadata
- `/api/rest/v4/recap-fetch/`: Fetch PACER documents
- `/api/rest/v4/recap-query/`: Query PACER data
- `/api/rest/v4/recap-email/`: Email processing

### 11. Citation Lookup API
**Endpoint**: `/api/rest/v4/citation-lookup/`
- **Method**: POST
- **Purpose**: Verify and lookup legal citations
- **Parameters**:
  - `text`: Text containing citations to parse
  - `citations`: Array of citation objects to lookup

### 12. Financial Disclosures APIs
- `/api/rest/v4/financial-disclosures/`: Main disclosure documents
- `/api/rest/v4/investments/`: Investment disclosures
- `/api/rest/v4/gifts/`: Gift disclosures
- `/api/rest/v4/debts/`: Debt disclosures
- `/api/rest/v4/agreements/`: Agreement disclosures

### 13. Alert APIs
- `/api/rest/v4/alerts/`: Search alerts
- `/api/rest/v4/docket-alerts/`: Docket tracking alerts

### 14. Visualization API
**Endpoint**: `/api/rest/v4/visualizations/`
- **Purpose**: Supreme Court case citation networks

### 15. Tags API
**Endpoint**: `/api/rest/v4/tags/`
- **Purpose**: Tag management for dockets

## Query Parameters & Filtering

### Common Filters
- **Exact match**: `?field=value`
- **Greater than**: `?field__gt=value`
- **Less than**: `?field__lt=value`
- **Range**: `?field__range=min,max`
- **Contains**: `?field__contains=value`
- **Starts with**: `?field__startswith=value`
- **Date filters**: Use ISO-8601 format (YYYY-MM-DD)
- **Exclusion**: Prepend with `!` (e.g., `?court__jurisdiction!=F`)

### Related Filters
Join filters across APIs using double underscores:
- `?cluster__docket__court=scotus` - Opinions from SCOTUS
- `?docket__court__jurisdiction=S` - Dockets from state courts

### Ordering
- **Ascending**: `?order_by=field`
- **Descending**: `?order_by=-field`
- **Multiple fields**: `?order_by=field1,-field2`

### Pagination
- **Standard**: `?page=2` (limited to 100 pages)
- **Deep pagination**: Use cursor-based pagination with `next` and `previous` URLs
- **Supported fields for deep pagination**: `id`, `date_modified`, `date_created`

### Field Selection
- **Include only specific fields**: `?fields=id,case_name`
- **Exclude fields**: `?omit=html,plain_text`
- **Nested fields**: Use double underscores (e.g., `?fields=cluster__case_name`)

### Counting
- **Get total count only**: `?count=on`
- Returns just the count without result data

## Response Format

### Standard Response Structure
```json
{
  "count": 12345,
  "next": "https://www.courtlistener.com/api/rest/v4/endpoint/?cursor=xyz",
  "previous": null,
  "results": [
    {
      "id": 1,
      "field1": "value1",
      "field2": "value2"
    }
  ]
}
```

### Serialization Formats
Set via `Accept` header:
- **JSON** (default): `application/json`
- **XML**: `application/xml`
- **HTML**: `text/html`

## New York State Court Identifiers

### Primary Courts (Consumer/Small Claims)
- **NYC Civil Court**: Various identifiers by borough
  - `ny-civ-ct`: General NYC Civil Court
  - Borough-specific identifiers available

- **Major City Courts**:
  - `ny-city-ct-buffalo`: Buffalo City Court
  - `ny-city-ct-rochester`: Rochester City Court
  - `ny-city-ct-syracuse`: Syracuse City Court
  - `ny-city-ct-albany`: Albany City Court
  - `ny-city-ct-yonkers`: Yonkers City Court

- **District Courts**:
  - `ny-dist-ct-nassau`: Nassau County District Court
  - `ny-dist-ct-suffolk`: Suffolk County District Court

### Secondary Courts (Appeals/Precedents)
- **Supreme Court**: `ny-supreme-ct` (and county variants)
- **Appellate Division**: `ny-app-div-1st` through `ny-app-div-4th`
- **Court of Appeals**: `ny-ct-app`

## Best Practices

### Performance Optimization
1. **Use field selection** to limit payload size
2. **Avoid unnecessary joins** (e.g., use `court=xyz` instead of `court__id=xyz`)
3. **Cache court data** - it rarely changes
4. **Use appropriate pagination** for large datasets
5. **Batch requests** when possible

### Error Handling
- **429 Too Many Requests**: Rate limit exceeded
- **401 Unauthorized**: Invalid or missing authentication
- **404 Not Found**: Resource doesn't exist
- **500 Server Error**: Internal server error

### Recommended Workflow for Case Law
1. Search using `/api/rest/v4/search/` to identify relevant cases
2. Get docket details from `/api/rest/v4/dockets/`
3. Retrieve clusters from `/api/rest/v4/clusters/`
4. Fetch full opinions from `/api/rest/v4/opinions/`

## Maintenance Windows
- **Weekly**: Thursday nights, 21:00-23:59 PT
- Check the public calendar for bulk processing schedules

## Additional Resources
- **OPTIONS Request**: Send OPTIONS request to any endpoint for detailed field information
- **Webhook Support**: Available for real-time updates
- **Bulk Data**: CSV files available for large-scale data needs
- **Database Replication**: PostgreSQL logical replication for enterprise needs

## Terms of Use
- Data is free of known copyright restrictions
- Public domain mark applies to most content
- Respect `blocked` flag for privacy-protected content
- One account per project/organization

## Support
- **GitHub Discussions**: https://github.com/freelawproject/courtlistener/discussions
- **Contact Form**: https://www.courtlistener.com/contact/
- **Documentation**: https://www.courtlistener.com/help/api/