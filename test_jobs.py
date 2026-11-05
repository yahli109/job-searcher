from jobs import Links, ats, comeet_jobs, matches

p = Links()
p.feed('<a href="/j/1"> Senior <b>Backend</b>\n Engineer </a><a href="/x"></a><a>no href</a>')
assert p.links == [("Senior Backend Engineer", "/j/1"), ("", "/x")], p.links

hosted = 'x COMPANY_POSITIONS_DATA = [{"name": "Buyer", "url_comeet_hosted_page": "https://c/b", "note": "a];b"}];\nmore'
assert comeet_jobs(hosted) == [("Buyer", "https://c/b")]
assert comeet_jobs("<html>no comeet here</html>") is None
# widget pages: uid/token found as "comeet_uid"/"comeet_token" (the API call itself is checked by the live run)
import jobs
calls = []
jobs.get = lambda url: calls.append(url) or '[{"name": "C++ Developer", "url_comeet_hosted_page": "https://c/1"}]'
assert comeet_jobs('var comeetvar={"comeet_token":"' + "A" * 20 + '","comeet_uid":"88.002"}') == [("C++ Developer", "https://c/1")]
assert calls[0].endswith("company/88.002/positions?token=" + "A" * 20), calls

assert matches("Senior Backend Engineer", ["engineer"])
assert not matches("Sales Lead", ["engineer"])
assert matches("Sales Lead", [])

assert ats("https://boards.greenhouse.io/anthropic") == ("greenhouse", "anthropic")
assert ats("https://job-boards.greenhouse.io/anthropic/jobs/123") == ("greenhouse", "anthropic")
assert ats("https://jobs.lever.co/palantir") == ("lever", "palantir")
assert ats("https://jobs.ashbyhq.com/notion") == ("ashby", "notion")
assert ats("https://www.wix.com/jobs") == ("html", None)
print("ok")
