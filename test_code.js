// Sample JavaScript code with various issues for testing

// Using var instead of let/const
var totalValue = 0;
var apiUrl = 'https://api.example.com';

// Missing semicolon
const MAX_RETRY = 3

// == instead of ===
function checkAuthorization(user) {
    // TODO: Implement proper authentication
    if (user.role == 'admin') {  // Using == instead of ===
        return true;
    }
    
    return false;
}

// Deeply nested callbacks
function fetchUserData(userId) {
    // Magic number
    if (userId < 1000) {
        return;
    }
    
    fetch(apiUrl + '/users/' + userId, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Network response was not ok');
        }
    })
    .then(userData => {
        fetch(apiUrl + '/permissions/' + userData.permissionId, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Network response was not ok');
            }
        })
        .then(permissionData => {
            fetch(apiUrl + '/roles/' + permissionData.roleId, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Network response was not ok');
                }
            })
            .then(roleData => {
                // Deeply nested callback
                processUserData(userData, permissionData, roleData);
            })
            .catch(error => {
                console.error('Error fetching role data:', error);
            });
        })
        .catch(error => {
            console.error('Error fetching permission data:', error);
        });
    })
    .catch(error => {
        console.error('Error fetching user data:', error);
    });
}

function processUserData(userData, permissionData, roleData) {
    var result = {  // Using var instead of const for object that won't be modified
        user: userData,
        permissions: permissionData,
        role: roleData
    }
    
    console.log('User data processed:', result);  // Missing semicolon
    
    // FIXME: Handle null values properly
    return result;
}

// Main function
function main() {
    var user = {  // Using var
        id: 12345,
        name: 'Test User',
        role: 'admin'
    };
    
    if (checkAuthorization(user) == true) {  // Using == instead of ===
        fetchUserData(user.id);
    }
}

// Call the main function
main() 