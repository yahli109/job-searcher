from jobs import Links, ats, matches

p = Links()
p.feed('<a href="/j/1"> Senior <b>Backend</b>\n Engineer </a><a href="/x"></a><a>no href</a>')
assert p.links == [("Senior Backend Engineer", "/j/1"), ("", "/x")], p.links

assert matches("Senior Backend Engineer", ["engineer"])
assert not matches("Sales Lead", ["engineer"])
assert matches("Sales Lead", [])

assert ats("https://boards.greenhouse.io/anthropic") == ("greenhouse", "anthropic")
assert ats("https://job-boards.greenhouse.io/anthropic/jobs/123") == ("greenhouse", "anthropic")
assert ats("https://jobs.lever.co/palantir") == ("lever", "palantir")
assert ats("https://jobs.ashbyhq.com/notion") == ("ashby", "notion")
assert ats("https://www.wix.com/jobs") == ("html", None)
print("ok")
