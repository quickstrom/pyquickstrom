# Getting Started Guide

We'll use the submitted artifact to reproduce the case study test results from "Quickstrom: Property-based acceptance testing with LTL specifications". It's
a Docker image that checks all (or only the specified) implementations of TodoMVC.

Requirements:

- Docker (preferrably installed directly on a Linux machine to avoid networking issues)
- A web browser to view test reports with

Getting started steps:

1. Load the image into Docker:

   ```bash
   docker load < case-study.tar.gz
   ```

2. Check a single TodoMVC application:

   ```bash
   docker run --network=host -v /tmp/case-study:/tmp/case-study case-study:firefox run-case-study backbone
   ```

   This will take about 1 minute. When finished, you should see some output
   ending with "Passed!".

3. Open `/tmp/case-study/backbone.firefox.1/html-report/index.html`. This is the
   report for the check, used for troubleshooting.

That's it, you're up and running!

# Step-by-Step Instructions

The case study runner has built-in expectations on the results of each
implemetation under test (see `case-studies/run.py` in the source for the full
listing). An expectation is either "passed", "failed", or "error". The runner
checks all implemetations sequentially and verifies that they match their
expected results.

Because an implementation can pass unexpectedly, which is likely with the most
intricate bugs that a check might not uncover, the runner retries up to 5 times.
An unexpected failure or error does not trigger retries.

Implementations that match the expected result are logged as:

```
Got expected RESULT!
```

while unexpected results are logged as:

```
Expected RESULT but result was RESULT!
```

At the end of the run, the runner lists the applications for which we didn't get
matching results, so that we can easily recheck only those.

## Checking all implementations

(This takes 20-30 minutes, typically.)

Similary to the _Getting Started Guide_, we use Docker to run the case study.
But this time we supply no argument, which means we check _all_ implementations:

```bash
docker run --network=host -v /tmp/case-study:/tmp/case-study case-study:firefox run-case-study
```

For each implementation, you'll see a header:

```
angular-dart
Browser: firefox
Stdout: /tmp/case-study/results/angular-dart.firefox.1/stdout.log
Stderr: /tmp/case-study/results/angular-dart.firefox.1/stderr.log
Interpreter log: /tmp/case-study/results/angular-dart.firefox.1/interpreter.log
Driver log: /tmp/case-study/results/angular-dart.firefox.1/driver.log
HTML report: /tmp/case-study/results/angular-dart.firefox.1/html-report/index.html
```

And for each try (or retry) you'll see a numbered check (this is the invocation of Quickstrom):

```
Try 1...
Command: quickstrom -I /nix/store/w80ikkbnxw760vjfqa260vya4jx7zs4i-case-studies --log-level=debug check todomvc http://localhost:12345/examples/angular2_es2015/index.html --browser=firefox --reporter=console --capture-screenshots --headless --reporter html --html-report-directory /tmp/case-study/results/angular2_es2015.firefox.1/html-report --interpreter-log-file /tmp/case-study/results/angular2_es2015.firefox.1/interpreter.log --driver-log-file /tmp/case-study/results/angular2_es2015.firefox.1/driver.log
```

If all goes well, the log ends with:

```
All results were as expected!
```

It is possible that not all results match. In particular, the bug we found in
`backbone_marionette` (Problem 11) is complex and it's not always found by
Quickstrom.

To rerun the check of an implementation, supply the name as an
argument:

```bash
docker run --network=host -v /tmp/case-study:/tmp/case-study case-study:firefox run-case-study backbone_marionette
```

## Claims from the paper

The runner's results support the claims from our case study in section 4.2:

* the distribution of passed and failed implementations, as summarized in Table 1
* the specific types of bugs as listed in Table 2

To verify that an implementation exhibits a specific bug, the test report (e.g.
`/tmp/case-study/backbone.firefox.1/html-report/index.html`) can be used to
introspect the trace and see screenshot and element states of each state. This
is a time-consuming process that we have not been able to automate.

In fact, our case study has since the paper submission found a few more faulty
implementations (`aurelia`, `canjs`, `canjs_require`). We'll update the paper to reflect the new
results.

## Source code

The full source code of the components is available on GitHub in two repositories:

* Specstrom
   - Repository: https://github.com/quickstrom/specstrom
   - Revision used: https://github.com/quickstrom/specstrom/tree/d5086152a818a10a9d07b747ef860dc17235235e
* Quickstrom
   - Repository: https://github.com/quickstrom/pyquickstrom
   - Revision used: https://github.com/quickstrom/pyquickstrom/tree/40e61e2e7caae5cb8c22bb910afd171c2758a7b9

## Installing from source

Installing the Quickstrom packages is a little fiddly, given the WebDriver and
browser dependencies, and that we have two components talking to eachother.

If using the Nix package manager, installing and running from source is rather easy:

```
git clone https://github.com/quickstrom/pyquickstrom.git
cd pyquickstrom
git checkout 40e61e2
cd case-studies
nix-shell
```

However, depending on your system the Firefox and Chrome packages might not be
supported. If so you'll have to install them in another way.

You can now run case studies directly on your machine:

```
./run.py /tmp/case-study-results
```