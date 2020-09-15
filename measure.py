#!/usr/bin/env python3

import os
import os.path
import subprocess
import sys
import time
import json
import urllib
import urllib.request


def p(str):
  print(str, flush=True)


def TODO(str):
  p("TODO: " + str + "\n\n\n\n")
  sys.exit(-1)


def build(dir):
  p("    Building")
  subprocess.run("./build.sh", cwd=dir)


def install(dir):
  p("    Fetching dependencies")
  subprocess.run("./install.sh", cwd=dir)


def start_server(dir):
  p("    Starting server")
  handle = subprocess.Popen("./exe", cwd=dir)
  time.sleep(2)
  return handle


def stop_server(dir, handle):
  p("    Stopping server")
  handle.kill()


def measure(dir, url):
  p("    Measuring")
  TODO("measure")


def warmup(dir, url):
  subprocess.run(["hey", "-n", "1000", "-c", "50", url])


def fizzbuzz():
  result = []
  for i in range(1, 101):
    if i % 15 == 0:
      result.append("fizzbuzz")
    elif i % 5 == 0:
      result.append("buzz")
    elif i % 3 == 0:
      result.append("fizz")
    else:
      result.append(str(i))
  return result


valid_response = fizzbuzz()


def test_output(dir, url):
  p("    Testing output")
  response = urllib.request.urlopen(url)
  body = response.read()
  answer = json.loads(body)
  return answer == valid_response


def get_url(dir):
  with open(dir + "/port", "r") as myfile:
    lines = myfile.readlines()
    port = "".join(lines)
    port = port.strip()
  return "http://localhost:" + port


def benchmark(dir):
  p("\n\n\n\n  Benchmarking " + dir)
  install(dir)
  build(dir)
  url = get_url(dir)
  handle = start_server(dir)
  try:
    if not test_output(dir, url):
      p("    Failed test")
    else:
      warmup(dir, url)
      results = measure(dir, url)
  finally:
    #  time.sleep(10000)
    stop_server(dir, handle)


p("Starting")
for f in os.listdir():
  if (os.path.isdir(f) and (not f.startswith("."))
      and (os.path.exists(f + "/build.sh"))):
    benchmark(f)