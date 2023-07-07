FROM alpine:3.18

# Install WINE and dependencies
RUN apk add \
	--repository http://dl-cdn.alpinelinux.org/alpine/v3.18/community/ \
	mingw-w64-gcc mingw-w64-binutils php82 \
	&& apk add --update-cache \
	xvfb openbox wine ncurses wine_gecko \
	figlet fortune \
	python3 perl nodejs php82 \
	bash fish zsh \
	build-base \
	&& addgroup -S user -g 81358 && adduser -S user -G user -u 81358

# Use the nonprivileged user we created
USER user

# Create wineprefix
# Wine waits at least three seconds after the last process quits before saving
# the registry and shutting down. Sleep a while to ensure the registry gets
# saved correctly.
RUN wineboot && sleep 20
