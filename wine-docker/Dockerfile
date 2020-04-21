FROM alpine:3

# Install WINE and dependencies
RUN apk add --update-cache xvfb openbox wine ncurses wine_gecko

# Create a nonprivileged user
RUN addgroup -S user && adduser -S user -G user
USER user

# Create wineprefix
# Wine waits three seconds after the last process quits before saving the
# registry and shutting down. Sleep 5 seconds to ensure the registry gets
# saved correctly.
RUN sh -c 'wineboot && sleep 5'
