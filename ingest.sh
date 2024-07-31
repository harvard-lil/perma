#!/usr/bin/env bash

display_usage() {
    echo "Seed dev database with data from a pg_dump file."
    echo
    echo "Usage:"
    echo "  bash ingest.sh -f dump_file"
}

# Help
if [[ ( $1 == "--help") ||  ($1 == "-h")]]; then
    display_usage
    exit 0
fi


getopts ":f:" opt || true;
case $opt in
    f)
        if [ -f "$OPTARG" ]
        then
            FILE=$OPTARG
        else
            echo "Invalid path."
            exit 1
        fi
        ;;
    \?)
        # illegal option or argument
        display_usage
        exit 1
        ;;
    :)
        # -f present, but no path provided
        echo "Please specify the path."
        exit 1
        ;;
esac
if [[ $((OPTIND - $#)) -ne 1 ]]; then
    # wrong number of args
    display_usage
    exit 1
fi

echo "Loading data from $FILE ..."
docker cp "$FILE" "$(docker compose ps -q db)":/tmp/data.dump
docker compose exec db pg_restore --username=perma --verbose --no-owner -h localhost -d perma /tmp/data.dump
docker compose exec db rm -f /tmp/data.dump
