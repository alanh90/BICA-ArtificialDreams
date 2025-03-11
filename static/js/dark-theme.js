document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const generateDayButton = document.getElementById('generate-day-button');
    const triggerDreamButton = document.getElementById('trigger-dream-button');
    const resetButton = document.getElementById('reset-button');
    const timelineEvents = document.getElementById('timeline-events');
    const eventsContainer = document.getElementById('events-container');
    const dreamStages = document.querySelectorAll('.dream-stage');
    const dreamNarration = document.getElementById('dream-narration');
    const dreamRecords = document.getElementById('dream-records');
    const consolidationVisualization = document.getElementById('consolidation-visualization');
    const memoryList = document.getElementById('memory-list');
    const dreamCanvas = document.getElementById('dream-visualization-canvas');
    
    // Metrics elements
    const totalMemoriesCount = document.getElementById('total-memories-count');
    const consolidatedMemoriesCount = document.getElementById('consolidated-memories-count');
    const insightsCount = document.getElementById('insights-count');
    
    // State
    let dreamingActive = false;
    let memories = [];
    let consolidatedMemories = [];
    let insights = [];
    let dailyEvents = [];
    let currentDreamStage = 'idle';
    let dreamSequence = null;
    
    // Canvas context
    let ctx = null;
    if (dreamCanvas) {
        ctx = dreamCanvas.getContext('2d');
    }
    
    // Debug logging
    console.log("DOM Content Loaded");
    console.log("Generate Day Button:", generateDayButton);
    console.log("Trigger Dream Button:", triggerDreamButton);
    
    // Initialize
    initializeTabs();
    setupEventListeners();
    updateMetrics();
    initializeCanvas();
    
    // Start polling for updates
    startPolling();
    
    // Event listeners
    function setupEventListeners() {
        console.log("Setting up event listeners");
        
        // Tab switching
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons
                tabButtons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                this.classList.add('active');
                
                // Hide all tab panes
                tabPanes.forEach(pane => pane.classList.remove('active'));
                // Show the corresponding tab pane
                const tabId = this.getAttribute('data-tab');
                document.getElementById(tabId).classList.add('active');
            });
        });
        
        // Generate new day
        if (generateDayButton) {
            console.log("Adding Generate Day button listener");
            generateDayButton.addEventListener('click', function() {
                console.log("Generate Day button clicked");
                generateNewDay();
            });
        }
        
        // Trigger dream
        if (triggerDreamButton) {
            console.log("Adding Trigger Dream button listener");
            triggerDreamButton.addEventListener('click', function() {
                console.log("Trigger Dream button clicked");
                triggerDream();
            });
        }
        
        // Reset system
        if (resetButton) {
            resetButton.addEventListener('click', resetSystem);
        }
        
        // Resize canvas when window resizes
        window.addEventListener('resize', resizeCanvas);
    }
    
    function initializeTabs() {
        // Activate first tab
        if (tabButtons && tabButtons.length > 0) {
            tabButtons[0].classList.add('active');
        }
        if (tabPanes && tabPanes.length > 0) {
            tabPanes[0].classList.add('active');
        }
    }
    
    function initializeCanvas() {
        if (!dreamCanvas) return;
        
        resizeCanvas();
        // Draw initial state
        drawIdleDreamState();
    }
    
    function resizeCanvas() {
        if (!dreamCanvas) return;
        
        const container = dreamCanvas.parentElement;
        if (!container) return;
        
        dreamCanvas.width = container.clientWidth * 0.6;
        dreamCanvas.height = container.clientHeight;
        
        // Redraw based on current state
        if (dreamingActive) {
            drawDreamingState();
        } else {
            drawIdleDreamState();
        }
    }
    
    // API Functions
    function startPolling() {
        console.log("Starting polling");
        // Poll for memory updates
        pollMemories();
        
        // Poll for dream state
        pollDreamState();
    }
    
    function pollMemories() {
        fetch('/api/memories')
            .then(response => response.json())
            .then(data => {
                console.log("Memories poll response:", data);
                updateMemories(data);
                setTimeout(pollMemories, 3000);
            })
            .catch(error => {
                console.error('Error polling memories:', error);
                setTimeout(pollMemories, 5000);
            });
    }
    
    function pollDreamState() {
        fetch('/api/dream/state')
            .then(response => response.json())
            .then(data => {
                console.log("Dream state poll response:", data);
                updateDreamState(data);
                
                // Poll dreams if needed
                if (data.dreaming) {
                    pollDreams();
                } else {
                    setTimeout(pollDreamState, 2000);
                }
            })
            .catch(error => {
                console.error('Error polling dream state:', error);
                setTimeout(pollDreamState, 5000);
            });
    }
    
    function pollDreams() {
        fetch('/api/dreams')
            .then(response => response.json())
            .then(data => {
                console.log("Dreams poll response:", data);
                updateDreams(data);
                
                // Continue polling at faster rate if dreaming
                setTimeout(pollDreams, 1000);
            })
            .catch(error => {
                console.error('Error polling dreams:', error);
                setTimeout(pollDreams, 3000);
            });
    }
    
    // Data Update Functions
    function updateMemories(data) {
        if (!data) return;
        
        if (data.regular) {
            memories = data.regular || [];
        }
        
        if (data.consolidated) {
            consolidatedMemories = data.consolidated || [];
        }
        
        if (data.insights) {
            insights = data.insights || [];
        }
        
        // Update UI
        updateMemoryList();
        updateMetrics();
    }
    
    function updateDreamState(data) {
        if (!data) return;
        
        // Update dream status indicator
        const statusValue = document.querySelector('.dream-status .status-value');
        if (!statusValue) return;
        
        if (data.dreaming) {
            statusValue.textContent = 'Dreaming';
            statusValue.style.color = 'var(--accent)';
            
            if (triggerDreamButton) {
                triggerDreamButton.disabled = true;
                triggerDreamButton.textContent = 'Dreaming...';
            }
            
            dreamingActive = true;
            
            // Update dream stage
            if (data.current_stage !== currentDreamStage) {
                setDreamStage(data.current_stage || 'idle');
            }
            
            // Draw dreaming state
            drawDreamingState();
        } else {
            statusValue.textContent = 'Idle';
            statusValue.style.color = 'var(--secondary)';
            
            if (triggerDreamButton) {
                triggerDreamButton.disabled = false;
                triggerDreamButton.textContent = 'Start Dreaming';
            }
            
            dreamingActive = false;
            
            // Reset dream stage
            setDreamStage('idle');
            
            // Draw idle state
            drawIdleDreamState();
        }
    }
    
    function updateDreams(data) {
        if (!dreamRecords) return;
        
        if (!data || data.length === 0) {
            dreamRecords.innerHTML = '<div class="empty-message">No dreams recorded yet.</div>';
            return;
        }
        
        // Update dream records
        dreamRecords.innerHTML = '';
        
        data.forEach(dream => {
            const dreamElement = document.createElement('div');
            dreamElement.classList.add('dream-record', 'fade-in');
            
            // Dream header
            const headerElement = document.createElement('div');
            headerElement.classList.add('dream-record-header');
            
            const timeElement = document.createElement('span');
            timeElement.textContent = dream.formatted_time || new Date(dream.timestamp * 1000).toLocaleString();
            
            const durationElement = document.createElement('span');
            durationElement.textContent = `Duration: ${dream.duration ? Math.round(dream.duration) + 's' : 'unknown'}`;
            
            headerElement.appendChild(timeElement);
            headerElement.appendChild(durationElement);
            
            // Dream content
            const contentElement = document.createElement('div');
            contentElement.classList.add('dream-record-content');
            
            // Add stages section
            if (dream.stages && dream.stages.length > 0) {
                const stagesElement = document.createElement('div');
                stagesElement.classList.add('dream-section');
                
                const stageTitle = document.createElement('div');
                stageTitle.classList.add('dream-section-title');
                stageTitle.textContent = 'Stages';
                
                const stagesItems = document.createElement('div');
                stagesItems.classList.add('dream-section-items');
                
                dream.stages.forEach(stage => {
                    const stageElement = document.createElement('div');
                    stageElement.classList.add('dream-section-item');
                    const stageTime = new Date((stage.timestamp || 0) * 1000).toLocaleTimeString();
                    stageElement.textContent = `${stageTime} - ${stage.description}`;
                    stagesItems.appendChild(stageElement);
                });
                
                stagesElement.appendChild(stageTitle);
                stagesElement.appendChild(stagesItems);
                contentElement.appendChild(stagesElement);
            }
            
            // Add consolidations section
            if (dream.consolidations && dream.consolidations.length > 0) {
                const consolidationsElement = document.createElement('div');
                consolidationsElement.classList.add('dream-section');
                
                const consolidationsTitle = document.createElement('div');
                consolidationsTitle.classList.add('dream-section-title');
                consolidationsTitle.textContent = 'Memory Consolidations';
                
                const consolidationsItems = document.createElement('div');
                consolidationsItems.classList.add('dream-section-items');
                
                dream.consolidations.forEach(consolidation => {
                    const consolidationElement = document.createElement('div');
                    consolidationElement.classList.add('dream-section-item');
                    consolidationElement.textContent = `Combined ${consolidation.count || 'multiple'} memories: ${consolidation.consolidated_text}`;
                    consolidationsItems.appendChild(consolidationElement);
                });
                
                consolidationsElement.appendChild(consolidationsTitle);
                consolidationsElement.appendChild(consolidationsItems);
                contentElement.appendChild(consolidationsElement);
            }
            
            // Add insights section
            if (dream.insights && dream.insights.length > 0) {
                const insightsElement = document.createElement('div');
                insightsElement.classList.add('dream-section');
                
                const insightsTitle = document.createElement('div');
                insightsTitle.classList.add('dream-section-title');
                insightsTitle.textContent = 'Insights Generated';
                
                const insightsItems = document.createElement('div');
                insightsItems.classList.add('dream-section-items');
                
                dream.insights.forEach(insight => {
                    const insightElement = document.createElement('div');
                    insightElement.classList.add('dream-section-item');
                    insightElement.textContent = `${insight.text} (Value: ${(insight.value || 0).toFixed(2)})`;
                    insightsItems.appendChild(insightElement);
                });
                
                insightsElement.appendChild(insightsTitle);
                insightsElement.appendChild(insightsItems);
                contentElement.appendChild(insightsElement);
            }
            
            dreamElement.appendChild(headerElement);
            dreamElement.appendChild(contentElement);
            dreamRecords.appendChild(dreamElement);
        });
        
        // Update consolidation visualization if we have dreams
        if (data.length > 0 && data[0].consolidations && data[0].consolidations.length > 0) {
            visualizeConsolidations(data[0].consolidations);
        }
    }
    
    function updateMemoryList() {
        if (!memoryList) return;
        
        const filter = document.getElementById('memory-filter')?.value || 'all';
        const searchText = document.getElementById('memory-search')?.value.toLowerCase() || '';
        
        // Combine all memory types
        let allMemories = [
            ...memories.map(m => ({...m, type: 'raw'})),
            ...consolidatedMemories.map(m => ({...m, type: 'consolidated'})),
            ...insights.map(m => ({...m, type: 'insight'}))
        ];
        
        // Apply filter
        if (filter !== 'all') {
            allMemories = allMemories.filter(m => m.type === filter);
        }
        
        // Apply search
        if (searchText) {
            allMemories = allMemories.filter(m => 
                m.text.toLowerCase().includes(searchText) ||
                (m.source && m.source.toLowerCase().includes(searchText))
            );
        }
        
        // Sort by recency
        allMemories.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
        
        // Update UI
        if (allMemories.length === 0) {
            memoryList.innerHTML = '<div class="empty-message">No memories found matching the criteria.</div>';
            return;
        }
        
        memoryList.innerHTML = '';
        
        allMemories.forEach(memory => {
            const memoryElement = document.createElement('div');
            memoryElement.classList.add('memory-item', `type-${memory.type}`);
            
            const headerElement = document.createElement('div');
            headerElement.classList.add('memory-header');
            
            const timeElement = document.createElement('span');
            timeElement.textContent = memory.formatted_time || new Date((memory.timestamp || 0) * 1000).toLocaleString();
            
            const sourceElement = document.createElement('span');
            sourceElement.textContent = memory.source || memory.type;
            
            headerElement.appendChild(timeElement);
            headerElement.appendChild(sourceElement);
            
            const contentElement = document.createElement('div');
            contentElement.classList.add('memory-content');
            contentElement.textContent = memory.text;
            
            memoryElement.appendChild(headerElement);
            memoryElement.appendChild(contentElement);
            
            // Add tags if any
            if (memory.metadata && Object.keys(memory.metadata).length > 0) {
                const tagsElement = document.createElement('div');
                tagsElement.classList.add('memory-tags');
                
                for (const [key, value] of Object.entries(memory.metadata)) {
                    if (value !== null && value !== undefined) {
                        const tagElement = document.createElement('span');
                        tagElement.classList.add('memory-tag');
                        tagElement.textContent = `${key}: ${value}`;
                        tagsElement.appendChild(tagElement);
                    }
                }
                
                memoryElement.appendChild(tagsElement);
            }
            
            memoryList.appendChild(memoryElement);
        });
    }
    
    function updateMetrics() {
        if (totalMemoriesCount) totalMemoriesCount.textContent = memories.length;
        if (consolidatedMemoriesCount) consolidatedMemoriesCount.textContent = consolidatedMemories.length;
        if (insightsCount) insightsCount.textContent = insights.length;
    }
    
    // Day Generator
    function generateNewDay() {
        console.log("Generating new day");
        
        if (generateDayButton) {
            generateDayButton.disabled = true;
            generateDayButton.textContent = 'Generating...';
        }
        
        // Clear existing events
        if (timelineEvents) timelineEvents.innerHTML = '';
        if (eventsContainer) eventsContainer.innerHTML = '';
        dailyEvents = [];
        
        // Create simple events - no complex logic that could fail
        const events = [
            {
                time: "07:30",
                type: "routine",
                content: "Morning coffee and checking emails",
                importance: 0.3
            },
            {
                time: "09:15",
                type: "encounter",
                content: "Met with Taylor at the coffee shop",
                importance: 0.6,
                similar_id: "coffee-meeting"
            },
            {
                time: "12:30",
                type: "routine",
                content: "Lunch break at desk",
                importance: 0.2
            },
            {
                time: "14:45",
                type: "observation",
                content: "Noticed the office plant needs water",
                importance: 0.4
            },
            {
                time: "16:30",
                type: "encounter",
                content: "Saw Taylor again in the elevator",
                importance: 0.6,
                similar_id: "coffee-meeting"
            },
            {
                time: "18:00",
                type: "routine",
                content: "Wrapped up work for the day",
                importance: 0.3
            }
        ];
        
        // Convert to our dailyEvents format
        events.forEach(event => {
            const [hour, minute] = event.time.split(':').map(Number);
            
            dailyEvents.push({
                time: event.time,
                type: event.type,
                content: event.content,
                hour: hour,
                minute: minute,
                importance: event.importance,
                similar_id: event.similar_id
            });
        });
        
        console.log("Created events:", dailyEvents);
        
        // Add events to UI
        renderDailyEvents();
        
        // Post events to backend
        postEventsToBackend(dailyEvents);
        
        // Re-enable button
        setTimeout(() => {
            if (generateDayButton) {
                generateDayButton.disabled = false;
                generateDayButton.textContent = 'Generate New Day';
            }
        }, 1000);
    }
    
    function renderDailyEvents() {
        console.log("Rendering daily events");
        
        if (!timelineEvents || !eventsContainer) {
            console.error("Timeline or events container not found");
            return;
        }
        
        // Add events to timeline and container
        dailyEvents.forEach((event, index) => {
            // Create timeline event
            const timelineEvent = document.createElement('div');
            timelineEvent.classList.add('timeline-event', `event-type-${event.type}`);
            
            // Calculate position
            const dayStart = 6; // 6 AM
            const dayEnd = 22;  // 10 PM
            const totalMinutes = (dayEnd - dayStart) * 60;
            const eventMinutes = (event.hour - dayStart) * 60 + event.minute;
            const positionPercent = (eventMinutes / totalMinutes) * 100;
            
            timelineEvent.style.left = `${positionPercent}%`;
            timelineEvent.textContent = event.time;
            timelineEvent.setAttribute('data-event-index', index);
            
            // Add click event
            timelineEvent.addEventListener('click', () => {
                // Highlight corresponding event in log
                const logEvent = document.querySelector(`.event-card[data-event-index="${index}"]`);
                if (logEvent) {
                    logEvent.classList.add('pulse');
                    setTimeout(() => {
                        logEvent.classList.remove('pulse');
                    }, 2000);
                    logEvent.scrollIntoView({ behavior: 'smooth' });
                }
            });
            
            timelineEvents.appendChild(timelineEvent);
            
            // Add event to container with animation delay
            setTimeout(() => {
                const eventCard = document.createElement('div');
                eventCard.classList.add('event-card', 'slide-in');
                eventCard.setAttribute('data-event-index', index);
                
                const timeElement = document.createElement('div');
                timeElement.classList.add('event-time');
                timeElement.textContent = event.time;
                
                const contentElement = document.createElement('div');
                contentElement.classList.add('event-content');
                contentElement.textContent = event.content;
                
                const tagElement = document.createElement('span');
                tagElement.classList.add('event-tag', `tag-${event.type}`);
                tagElement.textContent = event.type;
                
                eventCard.appendChild(timeElement);
                eventCard.appendChild(contentElement);
                eventCard.appendChild(tagElement);
                
                // Highlight similar events
                if (event.similar_id) {
                    const similarToElement = document.createElement('div');
                    similarToElement.classList.add('event-similar');
                    similarToElement.textContent = '(Similar to another event)';
                    eventCard.appendChild(similarToElement);
                    
                    // Add class for styling
                    eventCard.classList.add('similar-event');
                }
                
                eventsContainer.appendChild(eventCard);
            }, index * 100); // Staggered appearance
        });
    }
    
    function postEventsToBackend(events) {
        console.log("Posting events to backend");
        
        // Convert to memories for the backend
        const memories = events.map(event => ({
            text: `${event.time} - ${event.content}`,
            source: event.type,
            timestamp: new Date().getTime() / 1000,
            importance: event.importance || 0.5,
            metadata: {
                event_type: event.type,
                time: event.time,
                similar_to: event.similar_id || null
            }
        }));
        
        // Send to backend
        fetch('/api/memories/bulk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ memories })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Memories created:', data);
        })
        .catch(error => {
            console.error('Error creating memories:', error);
        });
    }
    
    // Dream Functions
    function triggerDream() {
        console.log("Triggering dream");
        
        if (triggerDreamButton) {
            triggerDreamButton.disabled = true;
            triggerDreamButton.textContent = 'Starting Dream...';
        }
        
        fetch('/api/dreams/trigger', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Dream triggered:', data);
            
            // Dream will be updated via polling
        })
        .catch(error => {
            console.error('Error triggering dream:', error);
            if (triggerDreamButton) {
                triggerDreamButton.disabled = false;
                triggerDreamButton.textContent = 'Start Dreaming';
            }
        });
    }
    
    function setDreamStage(stage) {
        console.log("Setting dream stage:", stage);
        currentDreamStage = stage;
        
        // Update stage indicators
        if (dreamStages) {
            dreamStages.forEach(elem => {
                elem.classList.remove('active');
                if (elem.getAttribute('data-stage') === stage) {
                    elem.classList.add('active');
                }
            });
        }
        
        // Update narration based on stage
        updateDreamNarration(stage);
    }
    
    function updateDreamNarration(stage) {
        if (!dreamNarration) return;
        
        let narration = '';
        
        switch (stage) {
            case 'idle':
                narration = '<p class="narration-text">The AI is not currently dreaming. Memories remain unprocessed and unconsolidated.</p>';
                break;
                
            case 'memory-selection':
                narration = `
                    <p class="narration-text">Selecting memories for processing...</p>
                    <p class="narration-text">Identifying similar memory patterns and repetitive events from the day.</p>
                    <p class="narration-text">Prioritizing memories based on importance, recency, and consolidation potential.</p>
                `;
                break;
                
            case 'consolidation':
                narration = `
                    <p class="narration-text">Consolidating similar memories...</p>
                    <p class="narration-text">Merging repeated encounters and observations into more efficient storage formats.</p>
                    <p class="narration-text">Extracting essential patterns while preserving unique details.</p>
                `;
                break;
                
            case 'hypothesis':
                narration = `
                    <p class="narration-text">Generating hypothetical scenarios based on memories...</p>
                    <p class="narration-text">Exploring potential future outcomes and implications.</p>
                    <p class="narration-text">Testing causal relationships between observed events.</p>
                `;
                break;
                
            case 'insight':
                narration = `
                    <p class="narration-text">Forming insights from analysis...</p>
                    <p class="narration-text">Connecting patterns across different memory categories.</p>
                    <p class="narration-text">Developing new understanding based on consolidated memories and hypothetical scenarios.</p>
                `;
                break;
                
            default:
                narration = '<p class="narration-text">Processing memories...</p>';
        }
        
        dreamNarration.innerHTML = narration;
    }
    
    // Canvas Drawing Functions
    function drawIdleDreamState() {
        if (!ctx) return;
        
        ctx.clearRect(0, 0, dreamCanvas.width, dreamCanvas.height);
        
        // Draw "idle" particles floating around
        const particles = [];
        const particleCount = 30;
        
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * dreamCanvas.width,
                y: Math.random() * dreamCanvas.height,
                radius: Math.random() * 3 + 1,
                color: `rgba(187, 134, 252, ${Math.random() * 0.5 + 0.1})`,
                speed: Math.random() * 0.5 + 0.1
            });
        }
        
        // Animation loop
        let animationFrameId;
        
        function animate() {
            if (!dreamingActive) {
                ctx.clearRect(0, 0, dreamCanvas.width, dreamCanvas.height);
                
                particles.forEach(particle => {
                    particle.y -= particle.speed;
                    
                    // Reset position if particle goes off screen
                    if (particle.y < -particle.radius) {
                        particle.y = dreamCanvas.height + particle.radius;
                        particle.x = Math.random() * dreamCanvas.width;
                    }
                    
                    // Draw particle
                    ctx.beginPath();
                    ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
                    ctx.fillStyle = particle.color;
                    ctx.fill();
                });
                
                animationFrameId = requestAnimationFrame(animate);
            } else {
                cancelAnimationFrame(animationFrameId);
            }
        }
        
        animate();
    }
    
    function drawDreamingState() {
        if (!ctx) return;
        
        // Cancel any existing animation
        if (dreamSequence) {
            cancelAnimationFrame(dreamSequence);
        }
        
        // Clear canvas
        ctx.clearRect(0, 0, dreamCanvas.width, dreamCanvas.height);
        
        // Draw based on current dream stage
        switch (currentDreamStage) {
            case 'memory-selection':
                drawMemorySelectionAnimation();
                break;
                
            case 'consolidation':
                drawConsolidationAnimation();
                break;
                
            case 'hypothesis':
                drawHypothesisAnimation();
                break;
                
            case 'insight':
                drawInsightAnimation();
                break;
                
            default:
                drawIdleDreamState();
        }
    }
    
    function drawMemorySelectionAnimation() {
        if (!ctx) return;
        
        const memoryNodes = [];
        const nodeCount = 20;
        
        // Create memory nodes
        for (let i = 0; i < nodeCount; i++) {
            memoryNodes.push({
                x: Math.random() * dreamCanvas.width,
                y: Math.random() * dreamCanvas.height,
                size: Math.random() * 20 + 10,
                color: `hsl(${Math.random() * 60 + 240}, 70%, 50%)`,
                speed: Math.random() * 2 + 0.5,
                direction: Math.random() * Math.PI * 2,
                selected: Math.random() > 0.6,
                alpha: 1
            });
        }
        
        function animate() {
            if (!ctx) return;
            
            ctx.clearRect(0, 0, dreamCanvas.width, dreamCanvas.height);
            
            // Draw connections between nodes
            ctx.globalAlpha = 0.2;
            memoryNodes.forEach((node, i) => {
                memoryNodes.forEach((otherNode, j) => {
                    if (i !== j) {
                        const dx = node.x - otherNode.x;
                        const dy = node.y - otherNode.y;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        
                        if (distance < 100) {
                            ctx.beginPath();
                            ctx.moveTo(node.x, node.y);
                            ctx.lineTo(otherNode.x, otherNode.y);
                            ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
                            ctx.lineWidth = 1;
                            ctx.stroke();
                        }
                    }
                });
            });
            
            // Draw nodes
            ctx.globalAlpha = 1;
            memoryNodes.forEach(node => {
                // Move node
                node.x += Math.cos(node.direction) * node.speed;
                node.y += Math.sin(node.direction) * node.speed;
                
                // Bounce off walls
                if (node.x < 0 || node.x > dreamCanvas.width) {
                    node.direction = Math.PI - node.direction;
                }
                if (node.y < 0 || node.y > dreamCanvas.height) {
                    node.direction = -node.direction;
                }
                
                // Highlight selected nodes
                if (node.selected) {
                    ctx.globalAlpha = 0.3;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, node.size + 5, 0, Math.PI * 2);
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
                    ctx.fill();
                    ctx.globalAlpha = 1;
                }
                
                // Draw node
                ctx.beginPath();
                ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
                ctx.fillStyle = node.color;
                ctx.fill();
            });
            
            if (dreamingActive && currentDreamStage === 'memory-selection') {
                dreamSequence = requestAnimationFrame(animate);
            }
        }
        
        animate();
    }
    
    function drawConsolidationAnimation() {
        if (!ctx) return;
        
        // Create groups of memory nodes that will consolidate
        const memoryGroups = [];
        const groupCount = 3;
        
        for (let g = 0; g < groupCount; g++) {
            const nodeCount = Math.floor(Math.random() * 3) + 2; // 2-4 nodes per group
            const centerX = Math.random() * (dreamCanvas.width * 0.6) + dreamCanvas.width * 0.2;
            const centerY = Math.random() * (dreamCanvas.height * 0.6) + dreamCanvas.height * 0.2;
            const groupColor = `hsl(${Math.random() * 60 + 240}, 70%, 50%)`;
            
            const nodes = [];
            for (let i = 0; i < nodeCount; i++) {
                const angle = (i / nodeCount) * Math.PI * 2;
                const distance = Math.random() * 50 + 50;
                
                nodes.push({
                    x: centerX + Math.cos(angle) * distance,
                    y: centerY + Math.sin(angle) * distance,
                    targetX: centerX,
                    targetY: centerY,
                    size: Math.random() * 10 + 10,
                    color: groupColor,
                    alpha: 1,
                    merged: false,
                    consolidateTime: Math.random() * 3000 + 1000 // Random start time for consolidation
                });
            }
            
            memoryGroups.push({
                nodes: nodes,
                centerX: centerX,
                centerY: centerY,
                consolidatedSize: 0,
                color: groupColor,
                alpha: 0
            });
        }
        
        const startTime = Date.now();
        
        function animate() {
            if (!ctx) return;
            
            ctx.clearRect(0, 0, dreamCanvas.width, dreamCanvas.height);
            
            const currentTime = Date.now();
            const elapsed = currentTime - startTime;
            
            memoryGroups.forEach(group => {
                // Draw connections between nodes in the group
                ctx.globalAlpha = 0.3;
                for (let i = 0; i < group.nodes.length; i++) {
                    for (let j = i + 1; j < group.nodes.length; j++) {
                        const nodeA = group.nodes[i];
                        const nodeB = group.nodes[j];
                        
                        if (!nodeA.merged && !nodeB.merged) {
                            ctx.beginPath();
                            ctx.moveTo(nodeA.x, nodeA.y);
                            ctx.lineTo(nodeB.x, nodeB.y);
                            ctx.strokeStyle = group.color;
                            ctx.lineWidth = 1;
                            ctx.stroke();
                        }
                    }
                }
                
                // Draw nodes
                ctx.globalAlpha = 1;
                group.nodes.forEach(node => {
                    if (elapsed > node.consolidateTime && !node.merged) {
                        // Move toward center
                        const dx = group.centerX - node.x;
                        const dy = group.centerY - node.y;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        
                        if (distance < 2) {
                            node.merged = true;
                            node.alpha = 0;
                            group.consolidatedSize += node.size * 0.7; // Consolidated node is smaller than sum of parts
                        } else {
                            node.x += dx * 0.05;
                            node.y += dy * 0.05;
                            node.alpha = Math.max(0, node.alpha - 0.01);
                        }
                    }
                    
                    if (!node.merged) {
                        ctx.globalAlpha = node.alpha;
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
                        ctx.fillStyle = node.color;
                        ctx.fill();
                    }
                });
                
                // Draw consolidated node if any nodes have merged
                const mergedCount = group.nodes.filter(n => n.merged).length;
                if (mergedCount > 0) {
                    group.alpha = Math.min(1, group.alpha + 0.02);
                    group.consolidatedSize = Math.max(15, group.nodes.reduce((sum, node) => sum + (node.merged ? node.size * 0.7 : 0), 0));
                    
                    ctx.globalAlpha = group.alpha;
                    ctx.beginPath();
                    ctx.arc(group.centerX, group.centerY, group.consolidatedSize, 0, Math.PI * 2);
                    ctx.fillStyle = group.color;
                    ctx.fill();
                    
                    // Draw "consolidated" label
                    if (group.alpha > 0.7) {
                        ctx.fillStyle = 'white';
                        ctx.font = '10px Inter';
                        ctx.textAlign = 'center';
                        ctx.fillText('Consolidated', group.centerX, group.centerY + group.consolidatedSize + 15);
                    }
                }
            });
            
            if (dreamingActive && currentDreamStage === 'consolidation') {
                dreamSequence = requestAnimationFrame(animate);
            }
        }
        
        animate();
    }
    
    function drawHypothesisAnimation() {
        if (!ctx) return;
        
        const memories = [];
        const memoryCount = 6;
        
        // Create memory nodes
        for (let i = 0; i < memoryCount; i++) {
            memories.push({
                x: Math.random() * dreamCanvas.width * 0.8 + dreamCanvas.width * 0.1,
                y: Math.random() * dreamCanvas.height * 0.8 + dreamCanvas.height * 0.1,
                size: Math.random() * 10 + 15,
                color: `hsl(${Math.random() * 60 + 240}, 70%, 50%)`
            });
        }
        
        // Create hypothetical scenarios
        const scenarios = [];
        const scenarioCount = 3;
        
        // Create scenarios
        for (let i = 0; i < scenarioCount; i++) {
            // Link to 2-3 random memories
            const linkedMemories = [];
            const linkCount = Math.floor(Math.random() * 2) + 2; // 2-3 links
            
            for (let j = 0; j < linkCount; j++) {
                const index = Math.floor(Math.random() * memoryCount);
                if (!linkedMemories.includes(index)) {
                    linkedMemories.push(index);
                }
            }
            
            scenarios.push({
                x: Math.random() * dreamCanvas.width * 0.6 + dreamCanvas.width * 0.2,
                y: Math.random() * dreamCanvas.height * 0.6 + dreamCanvas.height * 0.2,
                size: 0, // Will grow
                maxSize: Math.random() * 15 + 20,
                color: `hsl(${Math.random() * 60 + 120}, 70%, 50%)`, // Green hues
                linkedMemories: linkedMemories,
                activationTime: Math.random() * 2000 + 500
            });
        }
        
        const startTime = Date.now();
        
        function animate() {
            if (!ctx) return;
            
            ctx.clearRect(0, 0, dreamCanvas.width, dreamCanvas.height);
            
            const currentTime = Date.now();
            const elapsed = currentTime - startTime;
            
            // Draw memory nodes
            memories.forEach(memory => {
                ctx.beginPath();
                ctx.arc(memory.x, memory.y, memory.size, 0, Math.PI * 2);
                ctx.fillStyle = memory.color;
                ctx.fill();
                
                // Label
                ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
                ctx.font = '10px Inter';
                ctx.textAlign = 'center';
                ctx.fillText('Memory', memory.x, memory.y - memory.size - 5);
            });
            
            // Process scenarios
            scenarios.forEach(scenario => {
                if (elapsed > scenario.activationTime) {
                    // Grow scenario
                    if (scenario.size < scenario.maxSize) {
                        scenario.size += 0.2;
                    }
                    
                    // Draw connections to linked memories
                    scenario.linkedMemories.forEach(memoryIndex => {
                        const memory = memories[memoryIndex];
                        ctx.beginPath();
                        ctx.moveTo(scenario.x, scenario.y);
                        ctx.lineTo(memory.x, memory.y);
                        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
                        ctx.setLineDash([5, 3]); // Dashed line for hypothetical
                        ctx.lineWidth = 2;
                        ctx.stroke();
                        ctx.setLineDash([]);
                    });
                    
                    // Draw scenario node
                    ctx.beginPath();
                    ctx.arc(scenario.x, scenario.y, scenario.size, 0, Math.PI * 2);
                    ctx.fillStyle = scenario.color;
                    ctx.fill();
                    
                    // Label
                    if (scenario.size > scenario.maxSize * 0.7) {
                        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
                        ctx.font = '10px Inter';
                        ctx.textAlign = 'center';
                        ctx.fillText('Hypothesis', scenario.x, scenario.y);
                    }
                }
            });
            
            if (dreamingActive && currentDreamStage === 'hypothesis') {
                dreamSequence = requestAnimationFrame(animate);
            }
        }
        
        animate();
    }
    
    function drawInsightAnimation() {
        if (!ctx) return;
        
        const memoryGroups = [];
        const groupCount = 2;
        
        // Create groups of consolidated memories
        for (let g = 0; g < groupCount; g++) {
            const nodeCount = Math.floor(Math.random() * 2) + 2; // 2-3 nodes per group
            const groupX = dreamCanvas.width * (g === 0 ? 0.25 : 0.75);
            const groupY = dreamCanvas.height * 0.3;
            const groupColor = `hsl(${g === 0 ? 240 : 180}, 70%, 50%)`;
            
            const nodes = [];
            for (let i = 0; i < nodeCount; i++) {
                const angle = (i / nodeCount) * Math.PI + (g === 0 ? Math.PI : 0);
                const distance = 50;
                
                nodes.push({
                    x: groupX + Math.cos(angle) * distance,
                    y: groupY + Math.sin(angle) * distance,
                    size: Math.random() * 10 + 15,
                    color: groupColor
                });
            }
            
            memoryGroups.push({
                nodes: nodes,
                x: groupX,
                y: groupY,
                color: groupColor
            });
        }
        
        // Create insight node in the center bottom
        const insight = {
            x: dreamCanvas.width / 2,
            y: dreamCanvas.height * 0.7,
            size: 0,
            maxSize: 30,
            color: 'hsl(300, 70%, 50%)', // Purple hue for insight
            connections: [],
            pulsePhase: 0
        };
        
        // Create connections to memories
        memoryGroups.forEach(group => {
            group.nodes.forEach(node => {
                insight.connections.push({
                    node: node,
                    active: false,
                    activationTime: Math.random() * 3000 + 1000,
                    progress: 0
                });
            });
        });
        
        const startTime = Date.now();
        
        function animate() {
            if (!ctx) return;
            
            ctx.clearRect(0, 0, dreamCanvas.width, dreamCanvas.height);
            
            const currentTime = Date.now();
            const elapsed = currentTime - startTime;
            
            // Draw memory groups
            memoryGroups.forEach(group => {
                // Draw group nodes
                group.nodes.forEach(node => {
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
                    ctx.fillStyle = node.color;
                    ctx.fill();
                });
                
                // Draw group label
                ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
                ctx.font = '12px Inter';
                ctx.textAlign = 'center';
                ctx.fillText('Consolidated Memories', group.x, group.y - 80);
            });
            
            // Update and draw insight connections
            insight.connections.forEach(connection => {
                if (elapsed > connection.activationTime) {
                    connection.active = true;
                    connection.progress = Math.min(1, connection.progress + 0.01);
                    
                    const node = connection.node;
                    const startX = node.x;
                    const startY = node.y;
                    const endX = insight.x;
                    const endY = insight.y;
                    
                    // Draw path with animated gradient
                    const gradient = ctx.createLinearGradient(startX, startY, endX, endY);
                    gradient.addColorStop(0, connection.node.color);
                    gradient.addColorStop(1, insight.color);
                    
                    ctx.beginPath();
                    ctx.moveTo(startX, startY);
                    ctx.lineTo(
                        startX + (endX - startX) * connection.progress,
                        startY + (endY - startY) * connection.progress
                    );
                    ctx.strokeStyle = gradient;
                    ctx.lineWidth = 2;
                    ctx.stroke();
                    
                    // Grow insight when connections are forming
                    if (insight.size < insight.maxSize) {
                        insight.size += 0.1;
                    }
                }
            });
            
            // Draw insight node
            if (insight.size > 0) {
                // Pulsing effect
                insight.pulsePhase += 0.05;
                const pulseFactor = 1 + Math.sin(insight.pulsePhase) * 0.1;
                
                ctx.beginPath();
                ctx.arc(insight.x, insight.y, insight.size * pulseFactor, 0, Math.PI * 2);
                ctx.fillStyle = insight.color;
                ctx.fill();
                
                // Draw glow
                const glow = ctx.createRadialGradient(
                    insight.x, insight.y, insight.size * pulseFactor,
                    insight.x, insight.y, insight.size * pulseFactor * 1.5
                );
                glow.addColorStop(0, 'rgba(255, 255, 255, 0.3)');
                glow.addColorStop(1, 'rgba(255, 255, 255, 0)');
                
                ctx.beginPath();
                ctx.arc(insight.x, insight.y, insight.size * pulseFactor * 1.5, 0, Math.PI * 2);
                ctx.fillStyle = glow;
                ctx.fill();
                
                // Label
                ctx.fillStyle = 'white';
                ctx.font = '14px Inter';
                ctx.textAlign = 'center';
                ctx.fillText('Insight', insight.x, insight.y + 5);
            }
            
            if (dreamingActive && currentDreamStage === 'insight') {
                dreamSequence = requestAnimationFrame(animate);
            }
        }
        
        animate();
    }
    
    function visualizeConsolidations(consolidations) {
        if (!consolidationVisualization) return;
        
        // Clear previous visualization
        consolidationVisualization.innerHTML = '';
        
        // Visualize each consolidation group
        consolidations.forEach((consolidation, index) => {
            const count = consolidation.count || consolidation.original_memories?.length || 2;
            
            // Create a memory cluster visualization
            const clusterContainer = document.createElement('div');
            clusterContainer.classList.add('memory-cluster');
            clusterContainer.style.position = 'absolute';
            clusterContainer.style.left = `${Math.random() * 70 + 15}%`;
            clusterContainer.style.top = `${Math.random() * 70 + 15}%`;
            
            // Create the nodes
            for (let i = 0; i < count; i++) {
                const node = document.createElement('div');
                node.classList.add('memory-node');
                node.textContent = i + 1;
                
                // Position in a circle around the center
                const angle = (i / count) * Math.PI * 2;
                const distance = 70;
                node.style.left = `${Math.cos(angle) * distance + 100}px`;
                node.style.top = `${Math.sin(angle) * distance + 100}px`;
                
                // Add connection lines
                const connection = document.createElement('div');
                connection.classList.add('memory-connection');
                connection.style.width = `${distance}px`;
                connection.style.left = `${100}px`;
                connection.style.top = `${100}px`;
                connection.style.transform = `rotate(${angle}rad)`;
                
                clusterContainer.appendChild(connection);
                clusterContainer.appendChild(node);
                
                // Add animation with delay based on index
                setTimeout(() => {
                    node.style.transform = 'scale(1.1)';
                    setTimeout(() => {
                        node.style.transform = '';
                    }, 300);
                }, i * 300);
            }
            
            // Add the consolidated node in the center
            const consolidated = document.createElement('div');
            consolidated.classList.add('memory-node', 'consolidated');
            consolidated.textContent = 'C';
            consolidated.style.left = '100px';
            consolidated.style.top = '100px';
            consolidated.style.opacity = '0';
            
            // Animate consolidated node appearance
            setTimeout(() => {
                consolidated.style.opacity = '1';
                consolidated.style.transform = 'scale(1.3)';
                setTimeout(() => {
                    consolidated.style.transform = 'scale(1)';
                }, 500);
            }, count * 300 + 500);
            
            clusterContainer.appendChild(consolidated);
            consolidationVisualization.appendChild(clusterContainer);
        });
    }
    
    // System Functions
    function resetSystem() {
        if (!confirm('Are you sure you want to reset all systems? This will clear all memories, dreams, and other data.')) {
            return;
        }
        
        if (resetButton) {
            resetButton.disabled = true;
        }
        
        fetch('/api/system/reset', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            console.log('System reset:', data);
            
            // Reset local data
            memories = [];
            consolidatedMemories = [];
            insights = [];
            dailyEvents = [];
            
            // Clear UI
            if (timelineEvents) timelineEvents.innerHTML = '';
            if (eventsContainer) eventsContainer.innerHTML = '';
            if (dreamRecords) dreamRecords.innerHTML = '<div class="empty-message">No dreams recorded yet.</div>';
            if (memoryList) memoryList.innerHTML = '<div class="empty-message">No memories stored yet.</div>';
            if (consolidationVisualization) consolidationVisualization.innerHTML = '';
            
            // Reset dream state
            dreamingActive = false;
            setDreamStage('idle');
            drawIdleDreamState();
            
            // Update metrics
            updateMetrics();
            
            // Re-enable button
            if (resetButton) {
                resetButton.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error resetting system:', error);
            if (resetButton) {
                resetButton.disabled = false;
            }
        });
    }
});