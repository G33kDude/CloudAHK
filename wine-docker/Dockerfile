FROM alpine:3

# Install WINE and dependencies
RUN apk add --update-cache xvfb openbox wine ncurses wine_gecko

RUN apk add --update-cache figlet fortune

RUN apk add --update-cache python3 perl python2 nodejs php7

RUN apk add bash fish zsh

# Create a nonprivileged user
RUN addgroup -S user && adduser -S user -G user
USER user

# Create wineprefix
# Wine waits three seconds after the last process quits before saving the
# registry and shutting down. Sleep 5 seconds to ensure the registry gets
# saved correctly.
RUN sh -c 'wineboot && sleep 5'
