# Start from a tiny, minimal Linux distribution
FROM alpine:latest

# Update the package manager and install nmap
RUN apk update && apk add nmap

# Set the default command to be 'nmap'
ENTRYPOINT ["nmap"]