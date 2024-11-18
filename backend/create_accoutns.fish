#!/usr/bin/env fish

# Define the API endpoint
set API_URL "http://localhost:8000/api/auth/register/"

# Function to register a single user
function register_user
    set -l username $argv[1]
    set -l email "$username@amine.com"
    set -l password "Amine!123"

    # Create JSON payload with all required fields
    set -l json_data "{
        \"username\": \"$username\",
        \"email\": \"$email\",
        \"password\": \"$password\",
        \"confirm_password\": \"$password\",
        \"first_name\": \"Test\",
        \"last_name\": \"User$argv[1]\"
    }"

    echo "Attempting to register user: $username"
    echo "Request payload: $json_data"

    curl -X POST \
        -H "Content-Type: application/json" \
        -d "$json_data" \
        $API_URL

    # Add a delay between requests
    sleep 1
end

# Main script
echo "Starting user registration..."
echo "Target URL: $API_URL"
echo "-------------------"

# Register four users
for i in (seq 1 4)
    echo "\nRegistering user amine$i..."
    echo "-------------------"
    register_user "amine$i"
    echo "-------------------"
end

echo "\nRegistration process completed."
