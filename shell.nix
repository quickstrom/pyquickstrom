{ pkgs ? import <nixpkgs> {} }:
let
  specstrom = (import ../../specstrom {
    inherit pkgs;
    enableProfiling = true;
  }).specstrom;
  appEnv = pkgs.poetry2nix.mkPoetryEnv {
    projectDir = ./.;
    editablePackageSources = {
      my-app = ./.;
    };
  };
in
pkgs.mkShell {
  buildInputs = [ 
     pkgs.bashInteractive
    
     appEnv
  
     pkgs.geckodriver
     pkgs.chromedriver

     specstrom
  ];
}