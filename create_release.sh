#!/usr/bin/env bash
#Em caso de problemas com o script, registrar uma issue em:
#https://fontes.intranet.bb.com.br/aic/publico/atendimento/issues

function bump_version {
    echo "BUMP $1 version $2 with body '$3'"
    pushd sgs_caminho_critico || exit
    major=$(echo "$2" | cut -c1)
    minor=$(echo "$2" | cut -c3)
    fix=$(echo "$2" | cut -c5)
    dev=$(echo "$2" | cut -d "v" -f2)

    if [ "$1" == "major" ]; then
         new_version="$(( major + 1 )).0.0"
    elif [ "$1" == "minor" ]; then
        new_version="$major.$(( minor + 1 )).0"
    elif [ "$1" == "fix" ]; then
        new_version="$major.$minor.$(( fix + 1 ))"
    elif [ "$1" == "dev" ]; then
        if [ ${#dev} != 1 ]; then
            new_version="$major.$minor.$fix-dev1"
        else
            new_version="$major.$minor.$fix-dev$(( dev + 1))"
        fi
    fi

    sed -i "s/^__version__ = '.*'/__version__ = '$new_version'/g" __init__.py

    echo "New version updated to $new_version."
    git add __init__.py
    git commit -m "Bumped version number for v$new_version."
    git push
    git tag "v$new_version" -m "$body"
    git push --tags

    popd || exit
}

action=$1

if [ "$action" = "" ]; then
    echo "Help menu"
    echo
    echo "  Bump major version number for release: (1.2.3 -> 2.0.0)"
    echo "    ./create_release.sh major"
    echo
    echo "  Bump minor version number for release: (1.2.3 -> 1.3.0)"
    echo "    ./create_release.sh minor"
    echo
    echo "  Bump bug fixes version number for release: (1.2.3 -> 1.2.4)"
    echo "    ./create_release.sh fix"
    echo
    echo "  Bump version number for next development version (1.2.4 -> 1.2.4-dev1 or 1.2.4-dev1 -> 1.2.4-dev2)"
    echo "    ./create_release.sh dev"
    echo
    echo "  Bump and describe the release"
    echo "    ./create_release.sh dev -b 'FINALLY.'"
else
    version=$(python setup.py --version)
    if [ $# -le 2 ]; then
        body="Release da versao $version"
        echo "You didn't passed body description."
        echo "The release description will be $body."
        read -p "Are you sure? [Y|n]" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
           exit
        fi
    else
        body=$3
        echo "The release description will be > '$body'."
        read -p "Are you sure? [Y|n]" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            exit
        fi
    fi
    bump_version "$action" "$version" "$body"
fi
