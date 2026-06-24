# Extract version
VERSION=$(bumpver show -n --environ | grep CUR | awk '{gsub(/CURRENT_VERSION=/, ""); print}')

# Check if version include beta tag
if [[ $VERSION == *"b"* ]];
    then HAS_BETA_TAG=1;
    else HAS_BETA_TAG=0;
fi

# Evaluate version bumping request
case $1 in
    new-beta-major|new-beta-minor|new-beta-patch)
        rel=$(echo $1 | awk '{gsub(/new-beta-/, ""); print}')
        if [ $HAS_BETA_TAG -eq 0 ];
        then
            bumpver update -n --$rel --tag=beta
        else
            echo "You can create a new beta from a final version! Current version: $VERSION"; exit 1;
        fi
        ;;
    final)
        if [ $HAS_BETA_TAG -eq 1 ];
        then
            bumpver update -n --tag=final
        else
            echo "You can create a final version from a beta version! Current version: $VERSION"; exit 1;
        fi
        ;;
    upgrade-beta)
        if [ $HAS_BETA_TAG -eq 1 ];
        then
            bumpver update -n --tag-num
        else
            echo "You can upgrade a beta from a beta version! Current version: $VERSION"; exit 1;
        fi
        ;;
    major|minor|patch)
        bumpver update -n --$1 --tag=final
        ;;
esac
