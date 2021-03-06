#!/usr/bin/env python3

import os
import os.path
import subprocess
import sys
import time
import json
import urllib
import urllib.request
import re
import csv
import io


def p(str):
  print(str, flush=True)


def logfile(dir, title):
  return "logs/" + dir + "_" + title + ".log"


def run(dir, title, *args, **kwargs):
  logfilename = logfile(dir, title)
  with open(logfilename, "w") as file:
    result = subprocess.run(*args,
                            stdout=file,
                            stderr=subprocess.STDOUT,
                            **kwargs)
    if result.returncode != 0:
      raise Exception(
          f"Failure running {args} - see {logfilename} for details")
    return result


#def run_and_save(dir, title, *args, **kwargs):
#  with open(logfile(dir, title), "w") as file:
#    result = subprocess.check_output(*args, stderr=subprocess.STDOUT, **kwargs)
#    result = str(result)
#    file.write(result)
#    return result


def TODO(str):
  p("TODO: " + str + "\n\n\n\n")
  sys.exit(-1)


def build(dir):
  p("  Building")
  run(dir, "build", "./build.sh", cwd=dir)


def install(dir):
  p("  Fetching dependencies")
  run(dir, "install", "./install.sh", cwd=dir)


def start_server(dir):
  p("  Starting server")
  file = open(logfile(dir, "server"), "w")
  handle = subprocess.Popen("./exe",
                            cwd=dir,
                            stderr=subprocess.STDOUT,
                            stdout=file)
  time.sleep(2)
  return handle


def start_httpbin(dir):
  p("  Starting httpbin")
  file = open(logfile(dir, "httpbin"), "w")
  handle = subprocess.Popen(
      ["docker", "run", "-p", "1025:80", "kennethreitz/httpbin"],
      cwd=dir,
      stderr=subprocess.STDOUT,
      stdout=file)
  time.sleep(2)
  return handle


def stop_handle(name, dir, handle):
  p(f"  Stopping {name}")
  handle.kill()


def measure_fizzbuzz(dir, url):
  p("  Measuring fizzbuzz")
  run(dir, "measure_fizzbuzz", [
      "wrk", "--connections", "100", "--threads", "2", "--duration", "8",
      "--timeout", "20", url + "/fizzbuzz"
  ])


def measure_fizzboom(dir, url):
  p("  Measuring fizzboom")
  run(dir, "measure_fizzboom", [
      "wrk", "--connections", "10", "--threads", "2", "--duration", "10",
      "--timeout", "20", url + "/fizzboom"
  ])


def report(title, dir):
  results = {}

  with open(logfile(dir, title), "r") as file:
    for line in file.readlines():
      try:
        # general stats
        split = line.strip().split(":")
        if len(split) == 2:
          results[split[0]] = split[1].strip()
        else:
          # percentiles
          split = re.split("\\s+", line.strip())
          if len(split) > 1:
            results[split[0]] = [x.strip() for x in split[1:]]
          else:
            # status codes
            split = line.strip().split("]\t")
            if len(split) == 2:
              results[split[0][1:]] = split[1].strip()
            else:
              pass
      except Exception as e:
        print(f"Exception: {e}")
        pass
  errors = results.get("Socket errors", "N/A")

  print(f"    Reqs/s:       {results['Requests/sec']}")
  print(f"    Avg:       {results['Latency'][0]}")
  print(f"    Errors:      {errors}")
  #  print(f"    Fastest:   {results['Fastest'][]}")
  print(f"    Slowest:   {results['Latency'][2]}")


def report_fizzbuzz(dir):
  report("measure_fizzbuzz", dir)


def report_fizzboom(dir):
  report("measure_fizzboom", dir)


def warmup_fizzbuzz(dir, url):
  p("  Warming up")
  run(dir, "warmup", [
      "wrk", "--threads", "8", "--connections", "50", "--duration", "2",
      url + "/fizzbuzz"
  ])


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


def fizzboom():
  result = []
  for i in range(1, 101):
    if i % 15 == 0:
      result.append("")
    elif i % 5 == 0:
      result.append("buzz")
    elif i % 3 == 0:
      result.append("fizz")
    else:
      result.append(str(i))
  return result


def test_fizzbuzz(dir, url):
  p("  Testing fizzbuzz output")
  response = None
  body = None
  answer = None
  try:
    response = urllib.request.urlopen(url + "/fizzbuzz")
    body = response.read()
    answer = json.loads(body)
  except:
    p("Failed to read test output")
    p(f"Response {response}")
    p(f"Body {body}")
    p(f"Answer {answer}")

  equal = answer == fizzbuzz()
  if not equal:
    p(f"Error in fizzbuzz output: {answer}")
  return equal


def test_fizzboom(dir, url):
  p("  Testing fizzboom output")
  response = None
  body = None
  answer = None
  try:
    response = urllib.request.urlopen(url + "/fizzboom")
    body = response.read()
    answer = json.loads(body)
  except:
    p("Failed to read fizzboom output")
    p(f"Response {response}")
    p(f"Body {body}")
    p(f"Answer {answer}")

  equal = answer == fizzboom()
  if not equal:
    p(f"Error in fizzboom output: {answer}")
  return equal


def get_host(dir):
  with open(dir + "/port", "r") as myfile:
    lines = myfile.readlines()
    port = "".join(lines)
    port = port.strip()
  return "http://localhost:" + port


def is_broken(dir):
  return (os.path.exists(dir + "/BROKEN"))


def benchmark(dir):
  if is_broken(dir):
    p("Skipping broken benchmark: " + dir)
    return
  p("Benchmarking " + dir)
  install(dir)
  build(dir)
  host = get_host(dir)
  server_handle = start_server(dir)
  httpbin_handle = start_httpbin(dir)
  try:
    if not test_fizzbuzz(dir, host):
      p("  Failed fizzbuzz")
      return
    if not test_fizzboom(dir, host):
      p("  Failed fizzboom")
      return

    warmup_fizzbuzz(dir, host)
    measure_fizzbuzz(dir, host)
    report_fizzbuzz(dir)

    measure_fizzboom(dir, host)
    report_fizzboom(dir)
  finally:
    stop_handle("server", dir, server_handle)
    stop_handle("httpbin", dir, httpbin_handle)


if len(sys.argv) > 1:
  p(f"Benchmarking just {sys.argv[1:]}")
  for f in sys.argv[1:]:
    benchmark(f)
else:
  p("Starting entire benchmark")
  for f in os.listdir():
    if (os.path.isdir(f) and (not f.startswith("."))
        and (os.path.exists(f + "/build.sh"))):
      benchmark(f)

print("")
