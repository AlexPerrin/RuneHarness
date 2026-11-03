# The server image of one tree T: the installed server and its data (the built game cache), no key. `up` runs it with a
# key generated for the change; `ship` layers the live key on top (hash-checked, never printed) for the test server.
# Build context: the build copy's staged dir (server/ = server/app/build/install/app, data/ = .data minus keys and postgres).
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --chown=1000:1000 server/ /app/server/
COPY --chown=1000:1000 data/ /app/.data/
COPY --chown=1000:1000 game.yml /app/game.yml
USER 1000
ENV JAVA_OPTS=-Xmx2g
ENTRYPOINT ["/app/server/bin/app"]
