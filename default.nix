{
  nixpkgs ? import <nixpkgs> {},
  python ? nixpkgs.python36Full
}:

with nixpkgs;
with python.pkgs;

buildPythonPackage rec {
  name = "replacement";
  src = ./.;
  propagatedBuildInputs = [ ruamel_yaml ];
}
