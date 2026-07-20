def test_search_is_case_insensitive_partial_and_searches_notes(service):
    first = service.create("Write Release Notes", notes="Includes PourTask details")
    second = service.create("Other", notes="中文内容")
    from app.services.task_queries import search
    assert search([first, second], "release") == [first]
    assert search([first, second], "POURTASK") == [first]
    assert search([first, second], "中文") == [second]
    assert search([first, first], "write") == [first, first]
    assert search([first], "  ") == []
