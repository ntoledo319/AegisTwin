# Integrated System API Documentation

## Overview

This document provides comprehensive documentation for the Integrated System API, which allows you to interact with the system's data processing, analysis, digital twin, and knowledge graph capabilities.

## Base URL

All API endpoints are relative to the base URL:

```
http://localhost:8080/api
```

## Authentication

Most API endpoints require authentication. The API uses JWT (JSON Web Token) for authentication.

### Obtaining a Token

To obtain a token, send a POST request to the `/auth/login` endpoint:

```http
POST /auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

### Using the Token

Include the token in the `Authorization` header of your requests:

```http
Authorization: Bearer your_token_here
```

## API Endpoints

### User Management

#### Get All Users

```http
GET /users
```

Returns a list of all users.

**Response**

```json
{
  "users": [
    {
      "id": "user1",
      "username": "john_doe",
      "email": "john@example.com",
      "created_at": "2023-01-01T00:00:00Z",
      "last_login": "2023-01-02T10:30:00Z"
    },
    {
      "id": "user2",
      "username": "jane_smith",
      "email": "jane@example.com",
      "created_at": "2023-01-01T00:00:00Z",
      "last_login": "2023-01-02T11:45:00Z"
    }
  ]
}
```

#### Get User by ID

```http
GET /users/{user_id}
```

Returns information about a specific user.

**Response**

```json
{
  "id": "user1",
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2023-01-01T00:00:00Z",
  "last_login": "2023-01-02T10:30:00Z",
  "settings": {
    "theme": "dark",
    "notifications": true
  }
}
```

#### Create User

```http
POST /users
Content-Type: application/json

{
  "username": "new_user",
  "email": "new@example.com",
  "password": "secure_password"
}
```

Creates a new user.

**Response**

```json
{
  "id": "user3",
  "username": "new_user",
  "email": "new@example.com",
  "created_at": "2023-01-03T15:20:00Z"
}
```

#### Update User

```http
PUT /users/{user_id}
Content-Type: application/json

{
  "email": "updated@example.com",
  "settings": {
    "theme": "light"
  }
}
```

Updates a user's information.

**Response**

```json
{
  "id": "user1",
  "username": "john_doe",
  "email": "updated@example.com",
  "created_at": "2023-01-01T00:00:00Z",
  "last_login": "2023-01-02T10:30:00Z",
  "settings": {
    "theme": "light",
    "notifications": true
  }
}
```

#### Delete User

```http
DELETE /users/{user_id}
```

Deletes a user.

**Response**

```json
{
  "success": true,
  "message": "User deleted successfully"
}
```

### Data Management

#### Get Data Sources

```http
GET /data/sources
```

Returns a list of available data sources.

**Response**

```json
{
  "sources": [
    {
      "id": "email",
      "name": "Email",
      "description": "Import data from email accounts",
      "supported_providers": ["gmail", "outlook", "imap"]
    },
    {
      "id": "messages",
      "name": "Messages",
      "description": "Import data from messaging platforms",
      "supported_providers": ["whatsapp", "telegram", "signal"]
    },
    {
      "id": "calendar",
      "name": "Calendar",
      "description": "Import data from calendar services",
      "supported_providers": ["google", "outlook", "ical"]
    },
    {
      "id": "social",
      "name": "Social Media",
      "description": "Import data from social media platforms",
      "supported_providers": ["twitter", "linkedin", "facebook"]
    }
  ]
}
```

#### Import Data

```http
POST /data/import
Content-Type: application/json

{
  "source": "email",
  "options": {
    "provider": "gmail",
    "email": "user@example.com",
    "start_date": "2023-01-01",
    "end_date": "2023-01-31"
  }
}
```

Imports data from a specified source.

**Response**

```json
{
  "import_id": "import_12345",
  "status": "success",
  "message": "Started importing data from Gmail",
  "details": {
    "source": "email",
    "provider": "gmail",
    "estimated_completion_time": "2023-01-03T16:30:00Z"
  }
}
```

#### Get Import Status

```http
GET /data/import/{import_id}
```

Returns the status of a data import.

**Response**

```json
{
  "import_id": "import_12345",
  "status": "in_progress",
  "progress": 65,
  "message": "Importing emails from Gmail",
  "started_at": "2023-01-03T16:00:00Z",
  "estimated_completion_time": "2023-01-03T16:30:00Z"
}
```

#### Get Imported Data

```http
GET /data/imported
```

Returns a list of imported data sets.

**Response**

```json
{
  "imports": [
    {
      "id": "import_12345",
      "source": "email",
      "provider": "gmail",
      "status": "completed",
      "record_count": 1250,
      "imported_at": "2023-01-03T16:30:00Z"
    },
    {
      "id": "import_12346",
      "source": "messages",
      "provider": "whatsapp",
      "status": "completed",
      "record_count": 3500,
      "imported_at": "2023-01-04T10:15:00Z"
    }
  ]
}
```

### Analysis

#### Analyze Data

```http
POST /analysis
Content-Type: application/json

{
  "type": "comprehensive",
  "data_id": "import_12345",
  "options": {
    "include_communication_analysis": true,
    "include_advanced_analysis": true,
    "include_cognitive_analysis": true
  }
}
```

Analyzes imported data.

**Response**

```json
{
  "id": "analysis_12345",
  "status": "started",
  "message": "Analysis started",
  "estimated_completion_time": "2023-01-03T17:00:00Z"
}
```

#### Get Analysis Status

```http
GET /analysis/{analysis_id}
```

Returns the status of an analysis.

**Response**

```json
{
  "id": "analysis_12345",
  "status": "in_progress",
  "progress": 75,
  "message": "Performing cognitive analysis",
  "started_at": "2023-01-03T16:45:00Z",
  "estimated_completion_time": "2023-01-03T17:00:00Z"
}
```

#### Get Analysis Results

```http
GET /analysis/{analysis_id}/results
```

Returns the results of a completed analysis.

**Response**

```json
{
  "id": "analysis_12345",
  "status": "completed",
  "completed_at": "2023-01-03T17:00:00Z",
  "results": {
    "communication": {
      "patterns": {
        "frequency": {
          "avg_messages_per_day": 42,
          "peak_day": "Monday",
          "peak_hour": 10
        },
        "relationships": {
          "top_contacts": [
            {"contact": "jane@example.com", "message_count": 156, "sentiment": 0.8},
            {"contact": "bob@example.com", "message_count": 89, "sentiment": 0.6}
          ]
        }
      }
    },
    "advanced": {
      "nlp": {
        "sentiment": {
          "overall": 0.65,
          "trend": "stable"
        },
        "entities": {
          "people": ["Jane", "Bob", "Alice"],
          "organizations": ["Acme Inc.", "TechCorp"],
          "locations": ["New York", "San Francisco"]
        }
      },
      "temporal": {
        "trends": [
          {"topic": "project", "trend": "increasing"},
          {"topic": "meeting", "trend": "stable"}
        ]
      }
    },
    "cognitive": {
      "personality": {
        "traits": {
          "openness": 0.75,
          "conscientiousness": 0.82,
          "extraversion": 0.63,
          "agreeableness": 0.71,
          "neuroticism": 0.45
        }
      },
      "values": {
        "achievement": 0.85,
        "benevolence": 0.78,
        "self_direction": 0.82
      }
    }
  }
}
```

#### Get Insights

```http
GET /insights
```

Returns insights generated from analyses.

**Response**

```json
{
  "insights": [
    {
      "id": "insight_12345",
      "title": "Communication Pattern Detected",
      "description": "You tend to communicate more frequently on Monday mornings, with an average of 15 messages sent between 9-11 AM.",
      "category": "communication",
      "score": 0.85,
      "generated_at": "2023-01-03T17:15:00Z"
    },
    {
      "id": "insight_12346",
      "title": "Relationship Insight",
      "description": "Your communication with Jane shows high engagement and positive sentiment, suggesting a strong professional relationship.",
      "category": "relationship",
      "score": 0.78,
      "generated_at": "2023-01-03T17:15:00Z"
    }
  ]
}
```

### Digital Twin

#### Interact with Digital Twin

```http
POST /digital-twin/interact
Content-Type: application/json

{
  "input": "What are my most common topics of discussion?",
  "type": "message",
  "session_id": "session_12345"
}
```

Interacts with the digital twin.

**Response**

```json
{
  "text": "Based on your communication data, your most common topics of discussion are project planning (25%), team coordination (18%), and technical issues (15%). Would you like more details on any of these topics?",
  "entities": ["project planning", "team coordination", "technical issues"],
  "topics": ["work", "communication"],
  "metrics": {
    "engagement": 0.85,
    "personalization": 0.92
  },
  "metadata": {
    "session_id": "session_12345",
    "timestamp": "2023-01-03T17:30:00Z"
  }
}
```

#### Create Session

```http
POST /digital-twin/sessions
Content-Type: application/json

{
  "name": "Work Planning Session",
  "metadata": {
    "purpose": "project planning",
    "context": "preparing for Q1 goals"
  }
}
```

Creates a new digital twin interaction session.

**Response**

```json
{
  "session_id": "session_12346",
  "name": "Work Planning Session",
  "created_at": "2023-01-03T17:45:00Z",
  "status": "active",
  "metadata": {
    "purpose": "project planning",
    "context": "preparing for Q1 goals"
  }
}
```

#### Get Sessions

```http
GET /digital-twin/sessions
```

Returns a list of digital twin interaction sessions.

**Response**

```json
{
  "sessions": [
    {
      "session_id": "session_12345",
      "name": "General Conversation",
      "created_at": "2023-01-03T17:30:00Z",
      "last_interaction": "2023-01-03T17:35:00Z",
      "message_count": 5,
      "status": "active"
    },
    {
      "session_id": "session_12346",
      "name": "Work Planning Session",
      "created_at": "2023-01-03T17:45:00Z",
      "last_interaction": "2023-01-03T17:45:00Z",
      "message_count": 0,
      "status": "active"
    }
  ]
}
```

#### Get Conversation History

```http
GET /digital-twin/sessions/{session_id}/history
```

Returns the conversation history for a session.

**Response**

```json
{
  "session_id": "session_12345",
  "name": "General Conversation",
  "history": [
    {
      "id": "msg_1",
      "sender": "user",
      "text": "What are my most common topics of discussion?",
      "timestamp": "2023-01-03T17:30:00Z"
    },
    {
      "id": "msg_2",
      "sender": "twin",
      "text": "Based on your communication data, your most common topics of discussion are project planning (25%), team coordination (18%), and technical issues (15%). Would you like more details on any of these topics?",
      "timestamp": "2023-01-03T17:30:05Z"
    },
    {
      "id": "msg_3",
      "sender": "user",
      "text": "Tell me more about project planning discussions.",
      "timestamp": "2023-01-03T17:31:00Z"
    },
    {
      "id": "msg_4",
      "sender": "twin",
      "text": "Your project planning discussions primarily involve timeline coordination (40%), resource allocation (35%), and risk assessment (25%). These conversations typically occur with Jane, Bob, and Alice, with most discussions happening on Monday mornings.",
      "timestamp": "2023-01-03T17:31:05Z"
    }
  ]
}
```

#### End Session

```http
DELETE /digital-twin/sessions/{session_id}
```

Ends a digital twin interaction session.

**Response**

```json
{
  "session_id": "session_12345",
  "status": "ended",
  "ended_at": "2023-01-03T18:00:00Z",
  "summary": {
    "duration": 1800,
    "message_count": 10,
    "topics": ["project planning", "team coordination"]
  }
}
```

### Knowledge Graph

#### Get Entities

```http
GET /knowledge-graph/entities
```

Returns entities from the knowledge graph.

**Parameters**

- `type` (optional): Filter by entity type
- `query` (optional): Search query
- `limit` (optional): Maximum number of results (default: 10)

**Response**

```json
{
  "entities": [
    {
      "id": "entity_12345",
      "text": "Project Alpha",
      "type": "PROJECT",
      "properties": {
        "start_date": "2023-01-15",
        "status": "active"
      },
      "created_at": "2023-01-03T12:00:00Z"
    },
    {
      "id": "entity_12346",
      "text": "Jane Smith",
      "type": "PERSON",
      "properties": {
        "email": "jane@example.com",
        "role": "Project Manager"
      },
      "created_at": "2023-01-03T12:01:00Z"
    }
  ]
}
```

#### Get Entity

```http
GET /knowledge-graph/entities/{entity_id}
```

Returns information about a specific entity.

**Response**

```json
{
  "id": "entity_12345",
  "text": "Project Alpha",
  "type": "PROJECT",
  "properties": {
    "start_date": "2023-01-15",
    "status": "active",
    "description": "A project to develop the new product line"
  },
  "created_at": "2023-01-03T12:00:00Z",
  "updated_at": "2023-01-03T14:30:00Z"
}
```

#### Get Relationships

```http
GET /knowledge-graph/relationships
```

Returns relationships from the knowledge graph.

**Parameters**

- `type` (optional): Filter by relationship type
- `source_id` (optional): Filter by source entity ID
- `target_id` (optional): Filter by target entity ID
- `limit` (optional): Maximum number of results (default: 10)

**Response**

```json
{
  "relationships": [
    {
      "id": "rel_12345",
      "source_id": "entity_12346",
      "target_id": "entity_12345",
      "type": "MANAGES",
      "properties": {
        "since": "2023-01-15",
        "role": "Project Manager"
      },
      "created_at": "2023-01-03T12:05:00Z"
    },
    {
      "id": "rel_12346",
      "source_id": "entity_12347",
      "target_id": "entity_12345",
      "type": "WORKS_ON",
      "properties": {
        "since": "2023-01-15",
        "role": "Developer"
      },
      "created_at": "2023-01-03T12:06:00Z"
    }
  ]
}
```

#### Get Relationship

```http
GET /knowledge-graph/relationships/{relationship_id}
```

Returns information about a specific relationship.

**Response**

```json
{
  "id": "rel_12345",
  "source_id": "entity_12346",
  "source": {
    "id": "entity_12346",
    "text": "Jane Smith",
    "type": "PERSON"
  },
  "target_id": "entity_12345",
  "target": {
    "id": "entity_12345",
    "text": "Project Alpha",
    "type": "PROJECT"
  },
  "type": "MANAGES",
  "properties": {
    "since": "2023-01-15",
    "role": "Project Manager",
    "responsibility_level": "high"
  },
  "created_at": "2023-01-03T12:05:00Z",
  "updated_at": "2023-01-03T14:35:00Z"
}
```

#### Add Entity

```http
POST /knowledge-graph/entities
Content-Type: application/json

{
  "text": "Meeting: Q1 Planning",
  "type": "EVENT",
  "properties": {
    "date": "2023-01-10T09:00:00Z",
    "location": "Conference Room A",
    "description": "Quarterly planning meeting"
  }
}
```

Adds a new entity to the knowledge graph.

**Response**

```json
{
  "id": "entity_12348",
  "text": "Meeting: Q1 Planning",
  "type": "EVENT",
  "properties": {
    "date": "2023-01-10T09:00:00Z",
    "location": "Conference Room A",
    "description": "Quarterly planning meeting"
  },
  "created_at": "2023-01-03T18:30:00Z"
}
```

#### Add Relationship

```http
POST /knowledge-graph/relationships
Content-Type: application/json

{
  "source_id": "entity_12345",
  "target_id": "entity_12348",
  "type": "RELATED_TO",
  "properties": {
    "description": "Project planning meeting",
    "importance": "high"
  }
}
```

Adds a new relationship to the knowledge graph.

**Response**

```json
{
  "id": "rel_12347",
  "source_id": "entity_12345",
  "target_id": "entity_12348",
  "type": "RELATED_TO",
  "properties": {
    "description": "Project planning meeting",
    "importance": "high"
  },
  "created_at": "2023-01-03T18:35:00Z"
}
```

### Visualization

#### Create Chart

```http
POST /visualization/chart
Content-Type: application/json

{
  "chart_type": "bar",
  "data": {
    "x": ["Category A", "Category B", "Category C", "Category D", "Category E"],
    "y": [23, 45, 56, 78, 42]
  },
  "title": "Sample Bar Chart",
  "x_label": "Categories",
  "y_label": "Values"
}
```

Creates a chart visualization.

**Response**

```json
{
  "id": "viz_12345",
  "chart_type": "bar",
  "title": "Sample Bar Chart",
  "format": "png",
  "image_url": "/api/visualization/viz_12345.png",
  "image_base64": "data:image/png;base64,..."
}
```

#### Create Graph Visualization

```http
POST /visualization/graph
Content-Type: application/json

{
  "nodes": [
    {"id": 1, "label": "Node 1", "type": "person", "group": 1, "size": 10},
    {"id": 2, "label": "Node 2", "type": "person", "group": 1, "size": 10},
    {"id": 3, "label": "Node 3", "type": "organization", "group": 2, "size": 15}
  ],
  "edges": [
    {"source": 1, "target": 2, "type": "friend", "weight": 1},
    {"source": 1, "target": 3, "type": "member", "weight": 2}
  ],
  "title": "Sample Network Graph",
  "layout": "force"
}
```

Creates a graph visualization.

**Response**

```json
{
  "id": "viz_12346",
  "title": "Sample Network Graph",
  "format": "png",
  "image_url": "/api/visualization/viz_12346.png",
  "image_base64": "data:image/png;base64,...",
  "html_url": "/api/visualization/viz_12346.html"
}
```

#### Create Dashboard

```http
POST /visualization/dashboard
Content-Type: application/json

{
  "title": "Communication Analysis Dashboard",
  "components": [
    {
      "type": "chart",
      "title": "Message Frequency by Day",
      "chart_type": "bar",
      "data": {
        "x": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "y": [42, 35, 28, 45, 50]
      }
    },
    {
      "type": "chart",
      "title": "Sentiment Over Time",
      "chart_type": "line",
      "data": {
        "series": [
          {
            "label": "Sentiment",
            "x": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"],
            "y": [0.65, 0.72, 0.68, 0.75, 0.80]
          }
        ]
      }
    },
    {
      "type": "graph",
      "title": "Communication Network",
      "data": {
        "nodes": [
          {"id": 1, "label": "You", "group": 1, "size": 15},
          {"id": 2, "label": "Jane", "group": 2, "size": 10},
          {"id": 3, "label": "Bob", "group": 2, "size": 10}
        ],
        "links": [
          {"source": 1, "target": 2, "value": 5},
          {"source": 1, "target": 3, "value": 3},
          {"source": 2, "target": 3, "value": 1}
        ]
      }
    }
  ]
}
```

Creates a dashboard with multiple visualizations.

**Response**

```json
{
  "id": "dashboard_12345",
  "title": "Communication Analysis Dashboard",
  "html_url": "/api/visualization/dashboard_12345.html",
  "component_count": 3,
  "created_at": "2023-01-03T19:00:00Z"
}
```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of requests:

- `200 OK`: The request was successful.
- `201 Created`: The resource was successfully created.
- `400 Bad Request`: The request was invalid or malformed.
- `401 Unauthorized`: Authentication is required or failed.
- `403 Forbidden`: The authenticated user does not have permission to access the resource.
- `404 Not Found`: The requested resource was not found.
- `500 Internal Server Error`: An error occurred on the server.

Error responses include a JSON object with an `error` field that provides more information about the error:

```json
{
  "error": "Invalid request parameters",
  "details": "The 'source' field is required"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Rate limits are specified in the response headers:

- `X-RateLimit-Limit`: The maximum number of requests allowed per hour.
- `X-RateLimit-Remaining`: The number of requests remaining in the current rate limit window.
- `X-RateLimit-Reset`: The time at which the current rate limit window resets, in UTC epoch seconds.

If you exceed the rate limit, you will receive a `429 Too Many Requests` response.

## Pagination

For endpoints that return lists of resources, pagination is supported using the following query parameters:

- `page`: The page number (starting from 1).
- `per_page`: The number of items per page (default: 10, max: 100).

Pagination information is included in the response headers:

- `X-Total-Count`: The total number of items.
- `X-Page`: The current page number.
- `X-Per-Page`: The number of items per page.
- `X-Total-Pages`: The total number of pages.

## Versioning

The API version is specified in the URL path:

```
http://localhost:8080/api/v1/users
```

The current version is `v1`.

## Support

For support or questions about the API, please contact the system administrator or refer to the developer documentation.