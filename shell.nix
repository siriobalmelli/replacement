{
  nixpkgs ? import (builtins.fetchGit {
    url = "https://siriobalmelli@github.com/siriobalmelli-foss/nixpkgs.git";
    ref = "master";
    }) { },
}:

with nixpkgs;

mkShell {
  buildInputs = [

  ] ++ (with python3Packages; [

    # use venv to handle all Python deps for sane development
    # make SURE nix-shell is run with --pure to avoid seeing system python things
    python
    venvShellHook
  ]);

  venvDir = "venv";

  postShellHook = ''
    export SOURCE_DATE_EPOCH=315532800  # fix ZIP does not support timestamps before 1980
    alias pip="python -m pip"
  '';
}

