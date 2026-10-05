# Arcadium

BMS competitive chart system.

## How to run

Ensure Docker Desktop is installed, and node/npm

Clone `.env.example` and rename it to `.env`.
- Fill it with any information you'd like. Docker creates the database from this information.

In the root, run `npm run build` or `npm run build-verbose`.
- `build` Builds the docker container and all the services within.
- `build-verbose` does the same, but you can see all the parts being built. It does not give you terminal access back until you stop the process.

Run `npm run migrate` to run the database migrations.

Run `npm run seed` to get all chart data and other necessary data into the database.

## What is this?
Arcadium is an alternative way to experience BMS (a rhythm game). It is a competitive ladder where you are battling against charts. Both you and the charts you're playing have an ELO rating. And clearing charts increases your ELO while reducing the ELO of the charts you're playing.

You are given a seed and eventually an ELO. Then, when you queue, you are given a chart within a certain amount of ELO from you, as well as `12` minutes to clear the chart. If you clear within the allotted time, you gain ELO and the chart loses ELO. 

As you keep playing, the hope is you will continue to get a variety of charts to play, start improving at various skillsets, and try to grind and become a Grandmaster. 

This README will be further cleaned up with screenshots, and link, and more once the front end is built and we're actually live. This is currently heavily WIP!