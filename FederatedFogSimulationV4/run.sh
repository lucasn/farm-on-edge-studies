#!/bin/bash

run_simulation () {
    docker compose up -d --build

    previous_log=""
    while true; do
        log=`docker logs -n 1 data`

        if [ "$log" != "$previous_log" ]; then
            echo $log
            previous_log=$log
        fi

        if echo $log | grep "Data saved" -q ;  then
            docker compose down
            break
        fi

        sleep 0.1
    done
}

input_file="run_configs.txt"

echo "" > .env

while read line; do
    if [ -z "${line}" ]; then
        run_simulation
        echo "" > .env
    else
        echo $line >> .env  
    fi
done < $input_file

echo $line >> .env  

run_simulation