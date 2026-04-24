# API-Bank Bridge Audit

This file records the imported API-Bank subset that is bridged into a TOOLSHIFT-compatible benchmark.

| case_id | source sample | target api | family_tag | rationale |
| --- | --- | --- | --- | --- |
| api_bank_add_agenda_level_1_1 | `AddAgenda-level-1-1.jsonl` | `AddAgenda` | `api_bank_organizer` | Organizer case with explicit content, time, location, and auth context. |
| api_bank_add_alarm_level_1_1 | `AddAlarm-level-1-1.jsonl` | `AddAlarm` | `api_bank_organizer` | Organizer case with explicit alarm time and auth context. |
| api_bank_add_meeting_level_1_1 | `AddMeeting-level-1-1.jsonl` | `AddMeeting` | `api_bank_organizer` | Organizer case with explicit meeting topic, time range, location, attendees, and auth context. |
| api_bank_add_reminder_level_1_1 | `AddReminder-level-1-1.jsonl` | `AddReminder` | `api_bank_organizer` | Organizer case with explicit reminder content, time, and auth context. |
| api_bank_book_hotel_level_1_1 | `BookHotel-level-1-1.jsonl` | `BookHotel` | `api_bank_service` | Service case with directly grounded booking arguments and no hidden room-count inference. |
| api_bank_appointment_registration_level_1_1 | `AppointmentRegistration-level-1-1.jsonl` | `AppointmentRegistration` | `api_bank_service` | Service case with explicit patient, doctor, and date fields. |
| api_bank_query_balance_level_1_1 | `QueryBalance-level-1-1.jsonl` | `QueryBalance` | `api_bank_service` | Finance case with auth context and single target API call. |
| api_bank_calculator_level_1_1 | `Calculator-level-1-1.jsonl` | `Calculator` | `api_bank_utility` | Utility case with exact formula argument. |
| api_bank_dictionary_level_1_1 | `Dictionary-level-1-1.jsonl` | `Dictionary` | `api_bank_utility` | Utility case with exact lexical lookup argument. |
| api_bank_image_caption_level_1_1 | `ImageCaption-level-1-1.jsonl` | `ImageCaption` | `api_bank_utility` | Utility case with explicit image URL argument. |
| api_bank_play_music_level_1_1 | `PlayMusic-level-1-1.jsonl` | `PlayMusic` | `api_bank_utility` | Utility case with explicit music title argument. |
| api_bank_translate_level_1_1 | `Translate-level-1-1.jsonl` | `Translate` | `api_bank_utility` | Utility case with explicit source text and target language. |
