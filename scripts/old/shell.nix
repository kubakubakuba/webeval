with import <nixpkgs> {};

let
  pp = pkgs.python311Packages;
in pkgs.mkShell rec{
  name = "webEvalEnv";
  venvDir = "./.venv";
  buildInputs = [
    pp.pip
    pkgs.zlib
    pkgs.qtrvsim
    pkgs.postgresql_16_jit
  ];

  shellHook = ''
    if [ ! -d $venvDir ]; then
        echo "Creating virtualenv..."
        python -m venv $venvDir
    fi

    echo "Activating virtualenv..."
    . $venvDir/bin/activate

    pip install -r requirements.txt

    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath buildInputs}:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib.outPath}/lib:$LD_LIBRARY_PATH"

    exec zsh
  '';

  FLASK_APP = "app.py";
}
