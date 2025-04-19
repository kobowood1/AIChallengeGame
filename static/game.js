document.addEventListener('DOMContentLoaded', function() {
    // Get room ID from URL
    const params = getUrlParams();
    const roomId = params.room;
    
    if (!roomId) {
        window.location.href = '/';
        return;
    }
    
    // UI elements
    const waitingRoom = document.getElementById('waiting-room');
    const gameInProgress = document.getElementById('game-in-progress');
    const gameFinished = document.getElementById('game-finished');
    const roomIdDisplay = document.getElementById('room-id-display');
    const shareRoomCode = document.getElementById('share-room-code');
    const copyShareCodeBtn = document.getElementById('copy-share-code');
    const leaveRoomBtn = document.getElementById('leave-room-btn');
    const startGameBtn = document.getElementById('start-game-btn');
    const playerList = document.getElementById('player-list');
    const hostControls = document.getElementById('host-controls');
    const challengePrompt = document.getElementById('challenge-prompt');
    const challengeDifficulty = document.getElementById('challenge-difficulty');
    const testCases = document.getElementById('test-cases');
    const timeRemaining = document.getElementById('time-remaining');
    const playersStatus = document.getElementById('players-status');
    const playerStatus = document.getElementById('player-status');
    const playerScore = document.getElementById('player-score');
    const submitSolutionBtn = document.getElementById('submit-solution-btn');
    const winnerAnnouncement = document.getElementById('winner-announcement');
    const finalScores = document.getElementById('final-scores');
    const playAgainBtn = document.getElementById('play-again-btn');
    
    // Display room info
    roomIdDisplay.textContent = roomId;
    shareRoomCode.textContent = roomId;
    
    // Initialize CodeMirror editor
    const editor = CodeMirror(document.getElementById('code-editor-container'), {
        mode: 'javascript',
        theme: 'dracula',
        lineNumbers: true,
        indentUnit: 4,
        tabSize: 4,
        lineWrapping: true,
        autofocus: true,
        extraKeys: {
            'Tab': function(cm) {
                cm.replaceSelection('    ', 'end');
            }
        }
    });
    
    // Default policy recommendation template
    editor.setValue('# Refugee Education Policy Recommendations\n\n1. Language Support: \n\n2. Teacher Training: \n\n3. School Integration: \n\n4. Psychosocial Support: \n\n5. Curriculum Adaptation: \n');
    
    // Socket.IO connection
    const socket = connectSocket();
    let isHost = false;
    let deliberationState = null;
    let timerInterval = null;
    
    // Join the deliberation room when page loads
    socket.on('connect', () => {
        // If we have a player name in sessionStorage, use it to rejoin
        const username = sessionStorage.getItem('username') || 'Player_' + Math.floor(Math.random() * 1000);
        sessionStorage.setItem('username', username);
        
        // Join the room
        socket.emit('join_deliberation', { room_id: roomId, username });
        
        // Show loading overlay
        toggleLoading(true, 'Joining policy deliberation room...');
    });
    
    // Socket.IO event handlers
    socket.on('deliberation_joined', (data) => {
        // Hide loading overlay
        toggleLoading(false);
        showNotification('Joined policy deliberation room', 'success');
        
        // Store policy advisor ID
        sessionStorage.setItem('advisorId', data.advisor_id);
    });
    
    socket.on('game_state_update', (state) => {
        deliberationState = state;
        updateUI(state);
    });
    
    socket.on('advisor_joined', (data) => {
        showNotification(`${data.username} joined the policy deliberation`, 'info');
    });
    
    socket.on('advisor_left', (data) => {
        if (deliberationState && deliberationState.players && deliberationState.players[data.advisor_id]) {
            const username = deliberationState.players[data.advisor_id].username;
            showNotification(`${username} left the policy deliberation`, 'info');
        }
    });
    
    socket.on('deliberation_started', (data) => {
        deliberationState = data.state;
        updateUI(data.state);
        showNotification('Policy deliberation started!', 'success');
        startGameTimer(data.challenge.time_limit);
    });
    
    socket.on('policy_proposal_submitted', (result) => {
        if (result.success) {
            showNotification(`Policy proposal submitted! Score: ${result.score}`, 'success');
            playerStatus.textContent = 'Submitted';
            playerStatus.className = 'font-bold text-green-400';
            playerScore.textContent = result.score;
            submitSolutionBtn.disabled = true;
            submitSolutionBtn.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            showNotification(`Error: ${result.message}`, 'error');
        }
    });
    
    socket.on('deliberation_finished', (data) => {
        deliberationState = data.state;
        updateUI(deliberationState);
        clearInterval(timerInterval);
        showNotification('Policy deliberation finished!', 'success');
    });
    
    socket.on('error', (data) => {
        toggleLoading(false);
        showNotification(`Error: ${data.message}`, 'error');
    });
    
    // Button event handlers
    copyShareCodeBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(shareRoomCode.textContent)
            .then(() => {
                copyShareCodeBtn.innerHTML = '<i class="fas fa-check"></i>';
                setTimeout(() => {
                    copyShareCodeBtn.innerHTML = '<i class="fas fa-copy"></i>';
                }, 2000);
            })
            .catch(err => {
                console.error('Failed to copy room code: ', err);
            });
    });
    
    leaveRoomBtn.addEventListener('click', () => {
        socket.emit('leave_deliberation', { room_id: roomId });
        window.location.href = '/';
    });
    
    startGameBtn.addEventListener('click', () => {
        socket.emit('start_deliberation', { room_id: roomId });
        toggleLoading(true, 'Starting policy deliberation...');
    });
    
    submitSolutionBtn.addEventListener('click', () => {
        const policyProposal = editor.getValue();
        
        if (policyProposal.trim() === '') {
            showNotification('Please write a policy proposal before submitting', 'error');
            return;
        }
        
        socket.emit('submit_policy_proposal', { 
            room_id: roomId, 
            solution: policyProposal 
        });
        
        toggleLoading(true, 'Submitting policy proposal...');
        setTimeout(() => toggleLoading(false), 1000);
    });
    
    playAgainBtn.addEventListener('click', () => {
        // Reset the deliberation state
        socket.emit('start_deliberation', { room_id: roomId });
        toggleLoading(true, 'Starting new policy deliberation...');
    });
    
    // UI update function
    function updateUI(state) {
        const advisorId = sessionStorage.getItem('advisorId');
        
        // Determine if current player is host (first player in the room)
        const advisorIds = Object.keys(state.players);
        isHost = advisorIds.length > 0 && advisorIds[0] === advisorId;
        
        // Show/hide host controls
        if (isHost && state.state === 'waiting') {
            hostControls.classList.remove('hidden');
        } else {
            hostControls.classList.add('hidden');
        }
        
        // Update player list in waiting room
        updatePlayerList(state.players);
        
        // Update game view based on state
        if (state.state === 'waiting') {
            waitingRoom.classList.remove('hidden');
            gameInProgress.classList.add('hidden');
            gameFinished.classList.add('hidden');
        } else if (state.state === 'active') {
            waitingRoom.classList.add('hidden');
            gameInProgress.classList.remove('hidden');
            gameFinished.classList.add('hidden');
            
            // Update challenge information
            updateChallengeInfo(state.current_challenge);
            
            // Update player statuses
            updatePlayerStatuses(state.players);
            
            // Update current advisor's status
            if (state.players[advisorId]) {
                const status = state.players[advisorId].status;
                playerScore.textContent = state.players[advisorId].score;
                
                if (status === 'deliberating') {
                    playerStatus.textContent = 'Deliberating';
                    playerStatus.className = 'font-bold text-yellow-400';
                    submitSolutionBtn.disabled = false;
                    submitSolutionBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                } else if (status === 'submitted') {
                    playerStatus.textContent = 'Submitted';
                    playerStatus.className = 'font-bold text-green-400';
                    submitSolutionBtn.disabled = true;
                    submitSolutionBtn.classList.add('opacity-50', 'cursor-not-allowed');
                }
            }
        } else if (state.state === 'finished') {
            waitingRoom.classList.add('hidden');
            gameInProgress.classList.add('hidden');
            gameFinished.classList.remove('hidden');
            
            // Update winner announcement
            updateWinnerAnnouncement(state.winners, state.players);
            
            // Update final scores
            updateFinalScores(state.players);
        }
    }
    
    // Update player list in waiting room
    function updatePlayerList(players) {
        playerList.innerHTML = '';
        
        if (Object.keys(players).length === 0) {
            playerList.innerHTML = `
                <div class="p-4 bg-gray-700 rounded flex items-center">
                    <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white mr-3">
                        <i class="fas fa-user"></i>
                    </div>
                    <span class="flex-grow">Waiting for policy advisors...</span>
                </div>
            `;
            return;
        }
        
        Object.entries(players).forEach(([id, player], index) => {
            const isHost = index === 0;
            const badge = isHost ? 
                '<span class="ml-2 text-xs bg-yellow-600 text-white px-2 py-0.5 rounded">Host</span>' : '';
            
            const playerItem = document.createElement('div');
            playerItem.className = 'p-4 bg-gray-700 rounded flex items-center';
            playerItem.innerHTML = `
                <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white mr-3">
                    <i class="fas fa-user"></i>
                </div>
                <span class="flex-grow">${player.username}${badge}</span>
            `;
            
            playerList.appendChild(playerItem);
        });
    }
    
    // Update challenge information
    function updateChallengeInfo(challenge) {
        if (!challenge) return;
        
        // Set challenge prompt
        challengePrompt.textContent = challenge.prompt;
        
        // Set policy difficulty badge
        challengeDifficulty.className = 'inline-block px-3 py-1 rounded text-sm font-bold mb-3 bg-blue-600';
        challengeDifficulty.textContent = 'POLICY DELIBERATION';
        
        // Set policy domains instead of test cases
        testCases.innerHTML = '';
        
        // Add description
        const descriptionEl = document.createElement('div');
        descriptionEl.className = 'mb-4 p-3 bg-gray-700 rounded';
        descriptionEl.innerHTML = `<p>${challenge.description}</p>`;
        testCases.appendChild(descriptionEl);
        
        // Add policy domains if available
        if (challenge.policy_domains) {
            const domainsTitle = document.createElement('div');
            domainsTitle.className = 'font-bold mb-2';
            domainsTitle.textContent = 'Policy Domains to Address:';
            testCases.appendChild(domainsTitle);
            
            const domainsList = document.createElement('ul');
            domainsList.className = 'list-disc pl-5 mb-4';
            
            challenge.policy_domains.forEach(domain => {
                const domainItem = document.createElement('li');
                domainItem.textContent = domain;
                domainsList.appendChild(domainItem);
            });
            
            testCases.appendChild(domainsList);
        }
        
        // Add instructions
        const instructionsEl = document.createElement('div');
        instructionsEl.className = 'p-3 bg-blue-900 bg-opacity-30 rounded border-l-4 border-blue-500';
        instructionsEl.innerHTML = `
            <p class="font-bold mb-2">Instructions:</p>
            <p>1. Work with your team to develop comprehensive refugee education policies.</p>
            <p>2. Consider all policy domains and their interconnections.</p>
            <p>3. Listen to feedback from citizen representatives (AI agents).</p>
            <p>4. Craft your final policy document in the editor.</p>
            <p>5. Submit when ready or when the time expires.</p>
        `;
        testCases.appendChild(instructionsEl);
    }
    
    // Update advisor statuses in deliberation
    function updatePlayerStatuses(players) {
        playersStatus.innerHTML = '';
        
        Object.entries(players).forEach(([id, player]) => {
            const statusColor = getStatusColor(player.status);
            
            const playerStatusItem = document.createElement('div');
            playerStatusItem.className = 'flex items-center justify-between p-3 bg-gray-700 rounded';
            playerStatusItem.innerHTML = `
                <div class="flex items-center">
                    <div class="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white mr-2">
                        <i class="fas fa-user text-xs"></i>
                    </div>
                    <span>${player.username}</span>
                </div>
                <div class="flex items-center">
                    <span class="mr-3">Score: ${player.score}</span>
                    <span class="${statusColor}">${formatStatus(player.status)}</span>
                </div>
            `;
            
            playersStatus.appendChild(playerStatusItem);
        });
    }
    
    // Update winner announcement
    function updateWinnerAnnouncement(winners, players) {
        if (!winners || winners.length === 0) {
            winnerAnnouncement.innerHTML = `
                <div class="text-2xl font-bold text-yellow-400 mb-2">It's a tie!</div>
                <p class="text-gray-300">Everyone did great!</p>
            `;
            return;
        }
        
        if (winners.length === 1) {
            const winnerId = winners[0];
            const winner = players[winnerId];
            
            winnerAnnouncement.innerHTML = `
                <div class="text-2xl font-bold text-yellow-400 mb-2">Winner!</div>
                <div class="flex justify-center items-center mb-4">
                    <div class="w-16 h-16 bg-yellow-600 rounded-full flex items-center justify-center text-white mr-3">
                        <i class="fas fa-trophy text-3xl"></i>
                    </div>
                </div>
                <p class="text-xl font-bold text-blue-400">${winner.username}</p>
                <p class="text-gray-300">with a score of ${winner.score}</p>
            `;
        } else {
            // Multiple winners (tie)
            const winnerNames = winners.map(id => players[id].username).join(', ');
            
            winnerAnnouncement.innerHTML = `
                <div class="text-2xl font-bold text-yellow-400 mb-2">It's a tie!</div>
                <div class="flex justify-center items-center mb-4">
                    <div class="w-16 h-16 bg-yellow-600 rounded-full flex items-center justify-center text-white mr-3">
                        <i class="fas fa-trophy text-3xl"></i>
                    </div>
                </div>
                <p class="text-xl font-bold text-blue-400">${winnerNames}</p>
                <p class="text-gray-300">with a score of ${players[winners[0]].score}</p>
            `;
        }
    }
    
    // Update final scores
    function updateFinalScores(players) {
        finalScores.innerHTML = '';
        
        // Sort players by score
        const sortedPlayers = Object.entries(players).sort((a, b) => b[1].score - a[1].score);
        
        sortedPlayers.forEach(([id, player], index) => {
            const rank = index + 1;
            const rankClass = rank === 1 ? 'text-yellow-400' : (rank === 2 ? 'text-gray-400' : (rank === 3 ? 'text-yellow-700' : 'text-gray-300'));
            
            const scoreItem = document.createElement('div');
            scoreItem.className = 'flex items-center justify-between p-3 bg-gray-700 rounded';
            scoreItem.innerHTML = `
                <div class="flex items-center">
                    <div class="w-6 h-6 ${rankClass} font-bold rounded-full flex items-center justify-center mr-2">
                        ${rank}
                    </div>
                    <span>${player.username}</span>
                </div>
                <div>
                    <span class="font-bold">${player.score}</span> points
                </div>
            `;
            
            finalScores.appendChild(scoreItem);
        });
    }
    
    // Helper function to get status color
    function getStatusColor(status) {
        switch (status) {
            case 'waiting':
                return 'text-gray-400';
            case 'deliberating':
                return 'text-yellow-400';
            case 'submitted':
                return 'text-green-400';
            case 'verified':
                return 'text-blue-400';
            default:
                return 'text-gray-300';
        }
    }
    
    // Helper function to format status text
    function formatStatus(status) {
        switch (status) {
            case 'waiting':
                return 'Waiting';
            case 'deliberating':
                return 'Deliberating';
            case 'submitted':
                return 'Submitted';
            case 'verified':
                return 'Verified';
            default:
                return status;
        }
    }
    
    // Start the deliberation timer
    function startGameTimer(seconds) {
        clearInterval(timerInterval);
        
        let timeLeft = seconds;
        timeRemaining.textContent = formatTime(timeLeft);
        
        timerInterval = setInterval(() => {
            timeLeft--;
            
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                timeLeft = 0;
                
                // Auto-submit if not submitted yet
                const advisorId = sessionStorage.getItem('advisorId');
                if (gameState && 
                    gameState.players && 
                    gameState.players[advisorId] && 
                    gameState.players[advisorId].status === 'deliberating') {
                    
                    const policyProposal = editor.getValue();
                    socket.emit('submit_policy_proposal', { 
                        room_id: roomId, 
                        solution: policyProposal 
                    });
                }
            }
            
            timeRemaining.textContent = formatTime(timeLeft);
            
            // Make timer flash red when low on time
            if (timeLeft <= 10) {
                timeRemaining.classList.toggle('text-red-500');
            }
        }, 1000);
    }
    
    // Request current deliberation state in case we missed any updates
    socket.emit('get_deliberation_state', { room_id: roomId });
});
