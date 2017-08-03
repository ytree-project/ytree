#!/usr/bin/env bash

if [ ! -d $HOME/ytree_test/rockstar ]; then
    girder-cli --api-url https://girder.hub.yt/api/v1 download 59835a1ee2a67400016a2cda $HOME/ytree_test
fi
