import re


text = """
Matching Modules
=================

   #  Name                                      Disclosure Date  Rank       Check  Description
   -  ----                                      ---------------  ----       -----  -----------
   0  exploit/multi/http/php_cgi_arg_injection  2012-05-03       excellent  Yes    PHP CGI Argument Injection

Interact with a module by name or index. For example info 0, use 0 or use exploit/multi/http/php_cgi_arg_injection
"""


pattern = r'exploit/[^ ]+'


matches = re.findall(pattern, text)


for match in matches:
    print(match)