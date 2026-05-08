# API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently no authentication required. Future versions will support:
- API Keys
- OAuth 2.0
- JWT Tokens

## Endpoints

### Health Check

#### GET /health
Check system health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Network Endpoints

#### GET /network
Get network information.

**Query Parameters:**
- `network_id` (string, optional): Network identifier

**Response:**
```json
{
  "id": "network_1",
  "name": "Test Network",
  "zones": 50,
  "nodes": 1000,
  "links": 1500,
  "modes": ["car", "transit", "walk", "bike"]
}
```

#### POST /network
Create new network.

**Request Body:**
```json
{
  "name": "New Network",
  "zones": [],
  "nodes": [],
  "links": []
}
```

**Response:**
```json
{
  "id": "network_2",
  "status": "created"
}
```

### Demand Endpoints

#### GET /demand
Get demand model information.

**Query Parameters:**
- `scenario_id` (string): Scenario identifier

**Response:**
```json
{
  "scenario": "scenario_1",
  "total_trips": 50000,
  "by_mode": {
    "car": 30000,
    "transit": 15000,
    "walk": 3000,
    "bike": 2000
  },
  "by_purpose": {
    "work": 25000,
    "school": 10000,
    "shopping": 8000,
    "other": 7000
  }
}
```

#### POST /demand
Run demand model.

**Request Body:**
```json
{
  "scenario_name": "scenario_1",
  "trip_rates": {"work": 0.5, "other": 0.3},
  "attraction_rates": {"work": 0.8, "other": 0.2},
  "time_periods": ["AM", "MD", "PM"]
}
```

**Response:**
```json
{
  "scenario_id": "scenario_1",
  "status": "completed",
  "total_trips": 50000
}
```

### Assignment Endpoints

#### POST /assignment
Run network assignment.

**Request Body:**
```json
{
  "scenario_id": "scenario_1",
  "method": "user_equilibrium",
  "parameters": {
    "max_iterations": 100,
    "convergence_tolerance": 0.001
  }
}
```

**Response:**
```json
{
  "assignment_id": "UE_1",
  "method": "user_equilibrium",
  "convergence_achieved": true,
  "iterations": 45,
  "total_cost": 125000,
  "convergence_gap": 0.0008
}
```

### Analytics Endpoints

#### GET /analytics
Get analytics results.

**Query Parameters:**
- `scenario_id` (string): Scenario identifier
- `metrics` (string, optional): Comma-separated metric names

**Response:**
```json
{
  "scenario": "scenario_1",
  "performance": {
    "vmt": 150000,
    "vht": 3500,
    "average_speed": 42.85,
    "congestion_hours": 450
  },
  "accessibility": {
    "mean_accessibility": 45000,
    "gini_coefficient": 0.28
  },
  "environment": {
    "co2_emissions": 61500000,
    "nox_emissions": 127500,
    "pm25_emissions": 1800
  }
}
```

### Scenario Endpoints

#### GET /scenarios
List all scenarios.

**Query Parameters:**
- `limit` (integer, default: 20): Number of scenarios to return
- `offset` (integer, default: 0): Pagination offset

**Response:**
```json
{
  "scenarios": [
    {
      "id": "scenario_1",
      "name": "Base Case",
      "created_at": "2026-05-07T12:00:00Z",
      "status": "completed"
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

#### GET /scenarios/{scenario_id}
Get specific scenario details.

**Response:**
```json
{
  "id": "scenario_1",
  "name": "Base Case",
  "network_id": "network_1",
  "demand_id": "demand_1",
  "assignment_id": "UE_1",
  "created_at": "2026-05-07T12:00:00Z",
  "updated_at": "2026-05-07T13:30:00Z",
  "status": "completed"
}
```

#### POST /scenarios
Create new scenario.

**Request Body:**
```json
{
  "name": "Alternative Scenario",
  "network_id": "network_1",
  "description": "Scenario with transit enhancements"
}
```

**Response:**
```json
{
  "id": "scenario_2",
  "name": "Alternative Scenario",
  "status": "created"
}
```

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message",
  "status_code": 400,
  "error_code": "VALIDATION_ERROR"
}
```

### Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

## Rate Limiting

- No rate limits currently
- Future versions will implement rate limiting

## Pagination

List endpoints support pagination:
- `limit`: Maximum results (default: 20, max: 100)
- `offset`: Skip N results (default: 0)

## Response Format

All responses are in JSON format with consistent structure:

```json
{
  "data": {},
  "status": "success",
  "timestamp": "2026-05-07T12:00:00Z"
}
```

## Webhooks

Webhooks can be registered for scenario completion:

```json
{
  "event": "scenario.completed",
  "webhook_url": "https://example.com/webhook",
  "secret": "webhook_secret_key"
}
```
