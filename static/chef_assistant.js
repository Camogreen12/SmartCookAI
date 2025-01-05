class ChefAssistant {
    constructor() {
        this.isListening = false;
        this.recognition = null;
        this.currentInstructions = [];
        this.currentStep = 0;
        this.currentAudio = null;
        this.apiKey = 'sk_a3f5087191f1593440db8c25940c6bf7a32a97850b9b3292';
        this.voiceId = 'ErXwobaYiN019PkySvjV'; // Josh voice
        this.lastInteractionTime = Date.now();
        this.lastSpeechTime = Date.now();
        this.isSpeaking = false;
        this.minTimeBetweenResponses = 2000; // 2 seconds minimum between responses
        this.recipeName = '';
        this.conversationContext = {
            lastDiscussedStep: 0,
            lastTopic: '',
            lastAction: '',
            isDiscussingStep: false
        };
        this.personality = {
            name: 'Chef Josh',
            greetings: [
                "Hello! I'm Chef Josh, and I'll be guiding you through making {recipeName} today!",
                "Welcome to your cooking session! I'm Chef Josh, and I'll help you make a delicious {recipeName}!",
                "Hi there! I'm Chef Josh, and I'm excited to help you prepare {recipeName} step by step!"
            ],
            encouragements: [
                "You're doing great with this step!",
                "That's perfect! You're handling this like a pro!",
                "Excellent work! Your {recipeName} is coming along nicely!"
            ],
            transitions: [
                "Now that you've completed that step, let's move on to",
                "Great job! Next up is",
                "Perfect! Let's continue with"
            ]
        };
        
        // Initialize speech recognition
        if ('webkitSpeechRecognition' in window) {
            this.recognition = new webkitSpeechRecognition();
            this.recognition.continuous = true;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';
            
            // Main recognition handler with interrupt capability
            this.recognition.onresult = async (event) => {
                const command = event.results[event.results.length - 1][0].transcript.toLowerCase();
                console.log('Received command:', command);
                
                // If we're speaking, treat this as an interruption
                if (this.isSpeaking) {
                    console.log('Interrupting current speech');
                    window.speechSynthesis.cancel();
                    if (this.currentAudio) {
                        this.currentAudio.pause();
                        this.currentAudio.currentTime = 0;
                        this.currentAudio = null;
                    }
                    this.isSpeaking = false;
                }
                
                // Only process command if enough time has passed since last response
                if (Date.now() - this.lastSpeechTime >= this.minTimeBetweenResponses) {
                    // Check if this is likely the AI's own voice
                    if (!this.isLikelyOwnVoice(command)) {
                        await this.processCommand(command);
                    } else {
                        console.log('Ignored likely self-voice:', command);
                    }
                } else {
                    console.log('Skipping command due to minimum time between responses');
                }
            };

            // Add onend handler to restart recognition if still listening
            this.recognition.onend = () => {
                if (this.isListening) {
                    setTimeout(() => {
                        this.recognition.start();
                    }, 1000); // Wait 1 second before restarting
                }
            };
        }

        // Set up periodic check for user engagement
        setInterval(() => this.checkUserEngagement(), 30000); // Check every 30 seconds
    }

    isLikelyOwnVoice(command) {
        // Check if the command contains common phrases from the AI's responses
        const aiPhrases = [
            "hi there",
            "i'm your virtual chef",
            "i'm chef josh",
            "would you like me to",
            "you're doing great",
            "let's move on to",
            "here's an important tip",
            "just checking in"
        ];
        
        return aiPhrases.some(phrase => command.includes(phrase.toLowerCase()));
    }

    async speak(text) {
        try {
            if (this.isSpeaking) {
                console.log('Already speaking, cancelling current speech');
                window.speechSynthesis.cancel();
                if (this.currentAudio) {
                    this.currentAudio.pause();
                    this.currentAudio.currentTime = 0;
                    this.currentAudio = null;
                }
            }

            this.isSpeaking = true;
            console.log('Using browser speech synthesis...');
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.1;  // Slightly faster than default
            utterance.pitch = 1;   // Normal pitch
            utterance.volume = 1;  // Full volume

            // Pre-load voices to ensure they're available
            await new Promise((resolve) => {
                if (window.speechSynthesis.getVoices().length > 0) {
                    resolve();
                } else {
                    window.speechSynthesis.onvoiceschanged = () => resolve();
                }
            });

            // Use a male voice if available
            const voices = window.speechSynthesis.getVoices();
            const maleVoice = voices.find(voice => 
                voice.name.toLowerCase().includes('male') || 
                voice.name.toLowerCase().includes('guy') ||
                voice.name.toLowerCase().includes('david') ||
                voice.name.toLowerCase().includes('james')
            );
            if (maleVoice) {
                utterance.voice = maleVoice;
            }

            // Handle speech start
            utterance.onstart = () => {
                // Force volume to stay at maximum
                utterance.volume = 1;
            };

            // Handle speech boundary (word/sentence breaks)
            utterance.onboundary = () => {
                // Maintain maximum volume throughout
                utterance.volume = 1;
            };

            // Handle speech end
            utterance.onend = () => {
                this.isSpeaking = false;
                this.lastSpeechTime = Date.now();
            };

            // Handle speech error
            utterance.onerror = (e) => {
                console.error('Speech synthesis error:', e);
                this.isSpeaking = false;
                this.lastSpeechTime = Date.now();
            };

            // Ensure speech synthesis is ready
            window.speechSynthesis.cancel(); // Clear any pending speech
            await new Promise(resolve => setTimeout(resolve, 100)); // Small delay to ensure clean state
            window.speechSynthesis.speak(utterance);
            return true;
        } catch (error) {
            console.error('Error with speech synthesis:', error);
            this.isSpeaking = false;
            this.lastSpeechTime = Date.now();
            return false;
        }
    }

    // Initialize with recipe data
    initialize(recipeData) {
        console.log('Initializing with recipe data:', recipeData);
        this.currentInstructions = recipeData.instructions || window.instructions || [];
        this.currentStep = recipeData.currentStep || 0;
        this.recipeName = sessionStorage.getItem('recipeName') || 'your recipe';
        const greeting = this.getRandomGreeting().replace('{recipeName}', this.recipeName);
        this.speak(greeting);
    }

    // Start listening
    startListening() {
        if (!this.isListening) {
            this.isListening = true;
            this.recognition.start();
            this.lastInteractionTime = Date.now();
            this.speak(`Hi there! I'm your virtual chef, and I'll be guiding you through making ${this.recipeName}. We're currently on step ${this.currentStep + 1}. Would you like me to explain this step, or do you have any questions?`);
        }
    }

    checkUserEngagement() {
        if (!this.isListening) return;

        const timeSinceLastInteraction = Date.now() - this.lastInteractionTime;
        if (timeSinceLastInteraction > 60000) { // If more than 1 minute has passed
            this.speak(`Just checking in! We're on step ${this.currentStep + 1} of your ${this.recipeName}. Would you like me to repeat the current step or help you with anything?`);
            this.lastInteractionTime = Date.now();
        }
    }

    // Stop listening
    stopListening() {
        if (this.isListening) {
            this.isListening = false;
            this.recognition.abort();
            
            // Stop any ongoing speech
            if (this.currentAudio) {
                this.currentAudio.pause();
                this.currentAudio.currentTime = 0;
                this.currentAudio = null;
            }
            // Also stop any fallback speech synthesis
            window.speechSynthesis.cancel();
        }
    }

    // Handle speech recognition results
    async handleSpeechResult(event) {
        const last = event.results.length - 1;
        const command = event.results[last][0].transcript.toLowerCase();

        console.log('Recognized speech:', command);

        // Process the command
        await this.processCommand(command);
    }

    // Process voice commands
    async processCommand(command) {
        this.lastInteractionTime = Date.now();
        console.log('Processing command:', command);
        
        // Get current instructions from the window if not already set
        if (!this.currentInstructions || this.currentInstructions.length === 0) {
            this.currentInstructions = window.instructions || [];
        }

        // Handle "go back to step X" commands first
        if (command.match(/\b(go|going|get|let's go|lets go|take me|bring me)\s+back\s+to\s+step\s+\d+\b/i)) {
            const stepNumber = command.match(/\bstep\s+(\d+)\b/i);
            if (stepNumber) {
                const requestedStep = parseInt(stepNumber[1]) - 1; // Convert to 0-based index
                if (requestedStep >= 0 && requestedStep < this.currentInstructions.length) {
                    this.currentStep = requestedStep;
                    this.updateConversationContext(requestedStep, 'navigation', 'moved back to specific step');
                    this.explainCurrentStep();
                    return;
                }
            }
        }

        // Handle step explanation requests
        if (command.match(/\b(explain|tell me|what is|show me|go to|read)\s+step\s+\d+\b/i)) {
            const stepNumber = command.match(/\bstep\s+(\d+)\b/i);
            if (stepNumber) {
                const requestedStep = parseInt(stepNumber[1]) - 1; // Convert to 0-based index
                if (requestedStep >= 0 && requestedStep < this.currentInstructions.length) {
                    this.currentStep = requestedStep;
                    this.updateConversationContext(requestedStep, 'explanation', 'explaining specific step');
                    this.explainCurrentStep();
                    return;
                }
            }
        }

        // Step navigation commands
        if (command.includes('next step') || command.includes('move on to next step') || command.includes("let's continue")) {
            const currentStepToUse = this.conversationContext.isDiscussingStep ? 
                this.conversationContext.lastDiscussedStep : 
                this.currentStep;

            if (currentStepToUse < this.currentInstructions.length - 1) {
                const nextStep = currentStepToUse + 1;
                this.currentStep = nextStep;
                this.updateConversationContext(nextStep, 'navigation', 'moved to next step');
                this.speak(`${this.getRandomTransition()} step ${nextStep + 1}: ${this.currentInstructions[nextStep].action}`);
            } else {
                this.speak(`You've reached the final step of ${this.recipeName}! Would you like me to go over any previous steps?`);
            }
            return;
        }

        // Handle "go back" commands
        if (command.includes('previous step') || command.includes('go back')) {
            const currentStepToUse = this.conversationContext.isDiscussingStep ? 
                this.conversationContext.lastDiscussedStep : 
                this.currentStep;

            if (currentStepToUse > 0) {
                const prevStep = currentStepToUse - 1;
                this.currentStep = prevStep;
                this.updateConversationContext(prevStep, 'navigation', 'moved to previous step');
                this.speak(`Going back to step ${prevStep + 1}: ${this.currentInstructions[prevStep].action}`);
            } else {
                this.speak(`We're already at the first step of ${this.recipeName}. Would you like me to explain it again?`);
            }
            return;
        }

        // Only match explicit step references
        const stepMatch = command.match(/\b(step|number)\s+(\d+)\b/i);
        if (stepMatch && !command.includes('minute') && !command.includes('second')) {
            const requestedStep = parseInt(stepMatch[2]) - 1; // Convert to 0-based index
            if (requestedStep >= 0 && requestedStep < this.currentInstructions.length) {
                this.currentStep = requestedStep;
                this.updateConversationContext(requestedStep, 'navigation', 'moved to specific step');
                this.explainCurrentStep();
                return;
            }
        }

        // Handle timing-related questions without triggering step navigation
        if (command.includes('minute') || command.includes('second') || command.includes('hour')) {
            await this.answerGeneralQuestion(command);
            return;
        }

        if (command.includes('repeat step') || command.includes('current step')) {
            // Use the last discussed step if it exists, otherwise use currentStep
            const stepToExplain = this.conversationContext.isDiscussingStep ? 
                this.conversationContext.lastDiscussedStep : 
                this.currentStep;
            
            this.currentStep = stepToExplain;
            this.updateConversationContext(stepToExplain, 'explanation', 'repeating current step');
            this.explainCurrentStep();
            return;
        }

        // Progress check
        if (command.includes('how am i doing') || command.includes('am i doing this right')) {
            const currentStepToUse = this.conversationContext.isDiscussingStep ? 
                this.conversationContext.lastDiscussedStep : 
                this.currentStep;
            
            this.speak(`${this.getRandomEncouragement().replace('{recipeName}', this.recipeName)} We're on step ${currentStepToUse + 1} out of ${this.currentInstructions.length}. Would you like me to explain the current step again?`);
            return;
        }

        // Time check
        if (command.includes('how much longer') || command.includes('how many steps left')) {
            const remainingSteps = this.currentInstructions.length - this.currentStep;
            this.speak(`You're doing great! We have ${remainingSteps} steps remaining in your ${this.recipeName}. Would you like to hear what's coming up next?`);
            return;
        }

        // Recipe information commands
        if (command.includes('what ingredients')) {
            this.listIngredients();
            return;
        }
        if (command.includes('what equipment') || command.includes('what tools')) {
            this.listEquipment();
            return;
        }
        if (command.includes('how long') || command.includes('timing')) {
            this.explainTiming();
            return;
        }

        // Help and general questions
        if (command.includes('help') || command.includes('what can you do')) {
            this.explainCapabilities();
            return;
        }

        // If no specific command is matched, try to answer as a general question
        await this.answerGeneralQuestion(command);
    }

    updateConversationContext(step, topic, action) {
        this.conversationContext = {
            lastDiscussedStep: step,
            lastTopic: topic,
            lastAction: action,
            isDiscussingStep: true
        };
    }

    isQuestionRelatedToCurrentContext(question) {
        try {
            if (!this.currentInstructions || 
                !this.currentInstructions[this.currentStep] || 
                !this.currentInstructions[this.currentStep].action) {
                return false;
            }

            const currentStepText = this.currentInstructions[this.currentStep].action.toLowerCase();
            const questionWords = question.toLowerCase().split(' ');
            
            // Look for common words between the current step and the question
            const commonWords = questionWords.filter(word => 
                currentStepText.includes(word) && 
                word.length > 3 && // Ignore small words
                !['what', 'how', 'why', 'when', 'where', 'which', 'who'].includes(word)
            );

            return commonWords.length > 0;
        } catch (error) {
            console.error('Error in isQuestionRelatedToCurrentContext:', error);
            return false;
        }
    }

    explainCurrentStep() {
        try {
            // Ensure we have instructions
            if (!this.currentInstructions || this.currentInstructions.length === 0) {
                this.currentInstructions = window.instructions || [];
            }

            // Validate current step
            if (!this.currentInstructions || 
                this.currentInstructions.length === 0 || 
                this.currentStep < 0 || 
                this.currentStep >= this.currentInstructions.length) {
                this.speak(`I'm sorry, I can't find that step in the recipe for ${this.recipeName}. Please try another step number between 1 and ${this.currentInstructions.length}.`);
                return;
            }

            // Get the step information
            const step = this.currentInstructions[this.currentStep];
            if (!step || !step.action) {
                this.speak(`I'm sorry, I'm having trouble reading step ${this.currentStep + 1}. Please try another step.`);
                return;
            }

            // Update conversation context and explain the step
            this.updateConversationContext(this.currentStep, 'explanation', step.action);
            const response = `For step ${this.currentStep + 1} of your ${this.recipeName}, ${step.action}`;
            this.speak(response);

            // Add the note if it exists
            if (step.note) {
                setTimeout(() => {
                    this.speak(`Here's an important tip for this step: ${step.note}`);
                }, 1000);
            }
        } catch (error) {
            console.error('Error in explainCurrentStep:', error);
            this.speak(`I apologize, I'm having trouble reading step ${this.currentStep + 1}. Please try asking again.`);
        }
    }

    listIngredients() {
        const ingredients = JSON.parse(sessionStorage.getItem('ingredients') || '[]');
        if (ingredients.length === 0) {
            this.speak("I don't have the ingredient list available.");
            return;
        }

        this.speak("Here are the ingredients you'll need: " + ingredients.join(', '));
    }

    listEquipment() {
        // Get current instructions from the window if not already set
        if (!this.currentInstructions || this.currentInstructions.length === 0) {
            this.currentInstructions = window.instructions || [];
        }

        const equipment = window.extractEquipmentFromInstructions(this.currentInstructions);
        if (equipment.length === 0) {
            this.speak("I don't have the equipment list available.");
            return;
        }

        this.speak("You'll need these tools: " + equipment.join(', '));
    }

    explainTiming() {
        // Get current instructions from the window if not already set
        if (!this.currentInstructions || this.currentInstructions.length === 0) {
            this.currentInstructions = window.instructions || [];
        }

        if (!this.currentInstructions || !this.currentInstructions[this.currentStep]) {
            this.speak("I'm sorry, I can't find the current step. Please make sure the recipe is loaded correctly.");
            return;
        }

        const step = this.currentInstructions[this.currentStep];
        if (step.action.toLowerCase().includes('minute') || step.action.toLowerCase().includes('hour')) {
            this.speak("For this step: " + step.action);
        } else {
            this.speak("This step doesn't have specific timing instructions. Just proceed at a comfortable pace.");
        }
    }

    explainCapabilities() {
        this.speak(`
            I'm ${this.personality.name}, and I'm here to guide you through making ${this.recipeName}! I can:
            Guide you step by step through the recipe
            Tell you what ingredients and tools you need
            Provide timing information and cooking tips
            Answer any questions about the current step or the recipe
            Just ask me to move to the next step when you're ready, or ask for help if you need it!
            We're currently on step ${this.currentStep + 1} out of ${this.currentInstructions.length}.
        `);
    }

    // General question handling
    async answerGeneralQuestion(question) {
        if (!this.isListening) {
            return;
        }
        
        try {
            if (!this.currentInstructions || this.currentInstructions.length === 0) {
                this.currentInstructions = window.instructions || [];
            }

            // Special handling for timing questions
            if (question.toLowerCase().includes('how long') || 
                question.toLowerCase().includes('timing') || 
                question.toLowerCase().includes('minutes') || 
                question.toLowerCase().includes('time')) {
                
                // If we're in a step context, use that step for timing questions
                const stepToUse = this.conversationContext.isDiscussingStep ? 
                    this.conversationContext.lastDiscussedStep : 
                    this.currentStep;

                const response = await fetch('/api/ask_question', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        question: question,
                        recipe_name: sessionStorage.getItem('recipeName'),
                        current_step: stepToUse,
                        instructions: this.currentInstructions,
                        is_general_question: false,  // Force step-specific context for timing
                        conversation_context: {
                            current_step: stepToUse,
                            last_discussed_step: stepToUse,
                            last_topic: 'timing',
                            last_action: this.currentInstructions[stepToUse].action,
                            is_timing_question: true
                        }
                    })
                });

                const data = await response.json();
                if (data.status === 'success' && this.isListening) {
                    this.speak(data.answer);
                    return;
                }
            }

            // For non-timing questions, determine which step to reference
            const stepToReference = this.conversationContext.isDiscussingStep ? 
                this.conversationContext.lastDiscussedStep : 
                -1;

            const response = await fetch('/api/ask_question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: question,
                    recipe_name: sessionStorage.getItem('recipeName'),
                    current_step: stepToReference,
                    instructions: this.currentInstructions,
                    is_general_question: !this.conversationContext.isDiscussingStep,
                    conversation_context: {
                        current_step: this.currentStep,
                        last_discussed_step: this.conversationContext.lastDiscussedStep,
                        last_topic: this.conversationContext.lastTopic,
                        last_action: this.conversationContext.lastAction
                    }
                })
            });

            const data = await response.json();
            if (data.status === 'success' && this.isListening) {
                this.speak(data.answer);
                // Reset the discussion flag after answering unless it's clearly about the current step
                if (!this.isQuestionRelatedToCurrentContext(question)) {
                    this.conversationContext.isDiscussingStep = false;
                }
            } else if (this.isListening) {
                this.speak("I'm sorry, I'm not sure about that. Could you try asking in a different way?");
            }
        } catch (error) {
            console.error('Error:', error);
            if (this.isListening) {
                this.speak("I apologize, but I'm having trouble answering that question right now.");
            }
        }
    }

    // Helper methods
    getRandomGreeting() {
        return this.personality.greetings[Math.floor(Math.random() * this.personality.greetings.length)];
    }

    getRandomEncouragement() {
        return this.personality.encouragements[Math.floor(Math.random() * this.personality.encouragements.length)];
    }

    getRandomTransition() {
        return this.personality.transitions[Math.floor(Math.random() * this.personality.transitions.length)];
    }
}

// Create and export the chef assistant instance
window.chefAssistant = new ChefAssistant(); 