document.addEventListener('DOMContentLoaded', function() {
    const socket = io.connect(window.location.origin);
    const userId = '{{ current_user.id }}'; // Make sure this is rendered correctly
    const messagesDiv = document.getElementById('messages');
    const messageText = document.getElementById('message-text');
    const sendButton = document.getElementById('send-button');

    // Join the room for the current user
    socket.on('connect', function() {
        socket.emit('join', { room: `user_${userId}` });
    });

    // Handle new message from server
    socket.on('new_message', function(data) {
        const messageDiv = document.createElement('div');
        messageDiv.textContent = `From: ${data.sender_id} - ${data.message_text} (${data.timestamp})`;
        messagesDiv.appendChild(messageDiv);
    });

    // Send message
    sendButton.addEventListener('click', function() {
        const messageTextValue = messageText.value;
        fetch('/message/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({
                sender_id: userId,
                receiver_id: 2, // Update this with the correct receiver ID
                message_text: messageTextValue
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'Message sent') {
                messageText.value = '';
            }
        });
    });
});
