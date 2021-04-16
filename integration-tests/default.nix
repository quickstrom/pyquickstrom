{ pkgs ? import ../nix/nixpkgs.nix, browser ? "chrome" }:
let
  firefox-xvfb = pkgs.writeShellScriptBin "firefox" ''
    ${pkgs.xvfb_run}/bin/xvfb-run ${pkgs.firefox}/bin/firefox $@
  '';
  quickstrom = (import ../. { inherit pkgs; firefox = firefox-xvfb; });

  makeTest = { name, module, origin, options ? "", expectedExitCode }:
    pkgs.stdenv.mkDerivation {
      name = "quickstrom-integration-test-${name}";
      src = ./.;
      phases = [ "checkPhase" ];
      checkPhase = ''
        set +e
        mkdir -p $out

        # TODO: add ./failing and /passing includes later when required.
        quickstrom --log-level=INFO check ${module} ${origin} ${options} -I${
          ./other
        } --browser=${browser} | tee $out/test-report.log
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
      buildInputs = [ quickstrom ];
      __noChroot = browser == "chrome";
    };

  makeTests =
    pkgs.lib.mapAttrs (name: value: makeTest (value // { inherit name; }));

  todomvc = builtins.fetchTarball {
    url =
      "https://github.com/tastejs/todomvc/archive/41ba86db92336c11e56d425c5151b7ec2932be9a.tar.gz";
    # nix-prefetch-url --unpack <url>
    # sha256 = "1kwpzsslp8cnmdp435syjcfwn54f3fqssniwhr5lynv0a8sqplnx";
  };

in makeTests {
  todomvc-vue = {
    module = "todomvc";
    origin = "${todomvc}/examples/vue/index.html";
    options = "";
    expectedExitCode = 0;
  };
  todomvc-backbone = {
    module = "todomvc";
    origin = "${todomvc}/examples/vue/index.html";
    options = "";
    expectedExitCode = 0;
  };
  todomvc-react = {
    module = "todomvc";
    origin = "${todomvc}/examples/vue/index.html";
    options = "";
    expectedExitCode = 0;
  };
  todomvc-angularjs = {
    module = "todomvc";
    origin = "${todomvc}/examples/angularjs/index.html";
    options = "";
    expectedExitCode = 3;
  };
}
