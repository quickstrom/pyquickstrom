{ pkgs ? import ../nix/nixpkgs.nix, browser ? "chrome" }:
let
  quickstrom = (import ../. { inherit pkgs; });

  webdriver-deps = if browser == "chrome" then [pkgs.chromedriver pkgs.chromium] else [pkgs.geckodriver pkgs.firefox];

  makeTest = { name, module, origin, options ? "", expectedExitCode }:
    pkgs.stdenv.mkDerivation {
      name = "quickstrom-integration-test-${name}";
      src = ./.;
      phases = [ "checkPhase" ];
      checkPhase = ''
        set +e
        mkdir -p $out

        # TODO: add ./failing and /passing includes later when required.
        quickstrom --log-level=INFO -I${
          ../case-studies
        } check ${module} ${origin} ${options} --browser=${browser} --reporter=console --reporter=html --html-report-directory=$out/html-report | tee $out/test-report.log
        exit_code=$?

        if [ $exit_code == "${toString expectedExitCode}" ]; then
            echo "Expected exit code (${
              toString expectedExitCode
            }) was returned."
        else 
            cat geckodriver.log || echo "No geckodriver log"
            cat interpreter.log
            echo "Expected exit code ${
              toString expectedExitCode
            }, but $exit_code was returned."
            exit 1
        fi
      '';
      doCheck = true;
      buildInputs = [ quickstrom ] ++ webdriver-deps;
      __noChroot = true;
    };

  makeTests =
    pkgs.lib.mapAttrs (name: value: makeTest (value // { inherit name; }));

  todomvc = builtins.fetchTarball {
    url =
      "https://github.com/tastejs/todomvc/archive/41ba86db92336c11e56d425c5151b7ec2932be9a.tar.gz";
  };

in makeTests {
  todomvc-backbone = {
    module = "todomvc";
    origin = "${todomvc}/examples/backbone/index.html";
    options = "";
    expectedExitCode = 0;
  };
  todomvc-mithril = {
    module = "todomvc";
    origin = "${todomvc}/examples/mithril/index.html";
    options = "";
    expectedExitCode = 3;
  };
  todomvc-angularjs = {
    module = "todomvc";
    origin = "${todomvc}/examples/angularjs/index.html";
    options = "";
    expectedExitCode = 3;
  };
}
