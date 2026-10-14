# API reference

FastAPI generates the full OpenAPI specification and interactive Swagger UI at `/docs` while the backend is running. Business endpoints use the `/api/v1` prefix. Protected routes require `Authorization: Bearer <access_token>` unless documented otherwise.

| Area | Method and route | Access / purpose |
|---|---|---|
| Health | `GET /health` | Public service check |
| Authentication | `POST /api/v1/auth/register` | Public patient registration |
| Authentication | `POST /api/v1/auth/login` | Patient, doctor, or admin login |
| Authentication | `GET /api/v1/auth/me` | Current authenticated user |
| Authentication | `POST /api/v1/auth/logout` | Sign-out endpoint |
| Doctors | `GET /api/v1/doctors/` | Public doctor directory; supports filters |
| Doctors | `GET /api/v1/doctors/specializations` | Public specializations |
| Doctors | `GET /api/v1/doctors/{doctor_id}` | Public profile details |
| Doctors | `GET /api/v1/doctors/me/profile` | Doctor's own profile |
| Doctors | `PUT /api/v1/doctors/me/profile` | Update doctor's profile |
| Doctors | `PATCH /api/v1/doctors/me` | Partial profile update |
| Doctors | `GET /api/v1/doctors/me/analytics` | Doctor dashboard metrics |
| Availability | `POST /api/v1/availability` | Doctor publishes a slot |
| Availability | `GET /api/v1/doctors/{doctor_id}/availability` | Public available slots; optional date filter |
| Availability | `GET /api/v1/doctors/me/availability` | Doctor's own slots |
| Availability | `DELETE /api/v1/availability/{slot_id}` | Deactivate an eligible slot owned by the doctor |
| Appointments | `POST /api/v1/appointments` | Patient books a slot |
| Appointments | `GET /api/v1/appointments/me` | Current user's appointment list |
| Appointments | `GET /api/v1/appointments/my` | Patient appointment-list alias used by the frontend |
| Appointments | `GET /api/v1/appointments/doctor` | Doctor schedule alias used by the frontend |
| Appointments | `GET /api/v1/appointments/{appointment_id}` | Authorized appointment detail |
| Appointments | `POST /api/v1/appointments/{appointment_id}/cancel` | Cancel an eligible appointment |
| Appointments | `POST /api/v1/appointments/{appointment_id}/complete` | Assigned doctor completes a consultation |
| Appointments | `POST /api/v1/appointments/{appointment_id}/reschedule` | Reschedule an eligible booking |
| Prescriptions | `POST /api/v1/prescriptions/?appointment_id=...` | Assigned doctor creates a prescription |
| Prescriptions | `GET /api/v1/prescriptions/my` | Patient's own prescriptions |
| Prescriptions | `GET /api/v1/prescriptions/doctor` | Doctor's prescriptions |
| Prescriptions | `GET /api/v1/prescriptions/{prescription_id}` | Authorized prescription detail |
| Patient profile | `GET /api/v1/users/profile` | Patient profile |
| Patient profile | `PUT /api/v1/users/profile` | Update patient profile |
| Medical records | `POST /api/v1/medical-records/` | Patient uploads a record |
| Medical records | `GET /api/v1/medical-records/my` | Patient's records |
| Medical records | `GET /api/v1/medical-records/timeline` | Authorized record timeline |
| Medical records | `POST /api/v1/medical-records/share` | Patient shares a record with a doctor |
| Medical records | `GET /api/v1/medical-records/shared-with-me` | Doctor views records shared with them |
| Medical records | `GET /api/v1/medical-records/{record_id}/file` | Authorized file retrieval |
| Medical records | `DELETE /api/v1/medical-records/{record_id}` | Delete an eligible record |
| Reviews | `POST /api/v1/reviews/` | Patient submits a review |
| Reviews | `GET /api/v1/reviews/doctor/{doctor_id}` | Public approved doctor reviews |
| Reviews | `GET /api/v1/reviews/` | Administrative review listing |
| Reviews | `PUT /api/v1/reviews/{review_id}/approval` | Admin review moderation |
| Notifications | `GET /api/v1/notifications/` | Current user's notifications |
| Notifications | `GET /api/v1/notifications/unread-count` | Unread count |
| Notifications | `POST /api/v1/notifications/{notification_id}/read` | Mark one notification read |
| Notifications | `POST /api/v1/notifications/read-all` | Mark all current user's notifications read |
| Symptom guidance | `POST /api/v1/ai/symptom-check` | Optional general health information; requires provider configuration |
| Administration | `GET /api/v1/admin/dashboard` | Admin dashboard summary |
| Administration | `GET /api/v1/admin/doctors` | Admin doctor list |
| Administration | `POST /api/v1/admin/doctors` | Admin creates a doctor account |
| Administration | `PUT /api/v1/admin/doctors/{doctor_id}/approval` | Admin updates approval |
| Administration | `PUT /api/v1/admin/doctors/{doctor_id}/availability` | Admin toggles availability |
| Administration | `GET /api/v1/admin/appointments` | Admin appointment list |
| Administration | `GET /api/v1/admin/users` | Admin user list |
| Administration | `PUT /api/v1/admin/users/{user_id}/status` | Admin updates account status |

Request and response schemas in the OpenAPI document are authoritative. Routes enforce authentication, role restrictions, resource ownership, and input validation in the backend. Validation errors generally return `422`; unauthenticated requests return `401`; permission failures return `403`; inaccessible or missing resources return `404`; and state or uniqueness conflicts return `409`.
