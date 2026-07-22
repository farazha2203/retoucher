# قرارداد Deadline برای فرانت‌اند

فیلد `workflow.deadline` در Order و ProjectRequest منبع واحد نمایش مهلت مرحله است.

```json
{"at":"ISO-8601","state":"active|overdue|none|terminal","is_overdue":false,"stage":"editing","owner_role":"editor","timeout_action":"auto_reassign"}
```

فرانت باید شمارش معکوس را از `at` بسازد، ولی تصمیم timeout فقط در Backend انجام می‌شود. `owner_role` مسئول اقدام فعلی و `timeout_action` رفتار برنامه‌ریزی‌شده Backend است.
