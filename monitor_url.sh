#!/bin/bash

# config
URL_LIST=("https://opensubtitles.org")
PERIOD_IN_SECONDS=30

while true; do
    for url in "${URL_LIST[@]}"; do
        current_date=$(date)
        response=$(curl -s -w "http_code:%{http_code} time_total:%{time_total}" -o /dev/null $url)
        # http_code=$(echo "$response" | grep http_code | cut -d":" -f2)
        # time_total=$(echo "$response" | grep time_total | cut -d":" -f2)
        echo "$current_date - $url - $response"
        sleep $PERIOD_IN_SECONDS
    done
done