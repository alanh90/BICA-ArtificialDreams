import time
import threading
import random
import json
from datetime import datetime


class EmotionalSystem:
    def __init__(self, client, memory_system):
        """Initialize the emotional system

        Args:
            client: OpenAI client for emotion analysis
            memory_system: Reference to the MemorySystem for storing emotional memories
        """
        # OpenAI client
        self.client = client
        self.memory_system = memory_system

        # Emotion dimensions with intensity 0-1 (0 = none, 1 = maximum)
        self.emotions = {
            "joy": 0.0,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0,
            "surprise": 0.0,
            "trust": 0.0,
            "disgust": 0.0,
            "anticipation": 0.0
        }

        # Track thoughts, conversation, and emotion history
        self.thoughts = []
        self.conversation = []
        self.emotion_history = [self.emotions.copy()]
        self.last_interaction = time.time()

        # System parameters
        self.decay_rate = 0.95  # Emotion decay rate
        self.noise_magnitude = 0.015  # Random noise in emotions
        self.thought_frequency = 7  # Average seconds between thoughts
        self.update_frequency = 0.2  # How often to record emotion history

        # Start background processing
        self.running = True
        self.last_thought_time = time.time()
        self.last_update_time = time.time()
        self.last_micro_time = time.time()
        self.background_thread = threading.Thread(target=self._background_process)
        self.background_thread.daemon = True
        self.background_thread.start()

    def _background_process(self):
        """Run continuous background processing of emotions and thoughts"""
        while self.running:
            current_time = time.time()

            # Apply natural decay
            self._apply_decay(current_time - self.last_update_time)

            # Apply random noise to emotions
            self._apply_noise()

            # Apply micro-fluctuations for more natural movement
            if current_time - self.last_micro_time > 0.5:  # Every half second
                self._apply_micro_fluctuations()
                self.last_micro_time = current_time

            # Generate periodic thoughts
            elapsed = current_time - self.last_thought_time
            thought_due = elapsed > random.uniform(
                self.thought_frequency * 0.5,
                self.thought_frequency * 1.5
            )

            if thought_due:
                self._generate_thought(current_time)
                self.last_thought_time = current_time

            # Record emotion history more frequently
            if current_time - self.last_update_time > self.update_frequency:
                self.emotion_history.append(self.emotions.copy())
                if len(self.emotion_history) > 300:  # 5 minutes worth
                    self.emotion_history = self.emotion_history[-300:]
                self.last_update_time = current_time

            # Sleep briefly - shorter sleep for more responsive updates
            time.sleep(0.05)

    def _apply_decay(self, elapsed_time):
        """Decay emotions gradually toward 0"""
        # Calculate decay factor based on elapsed time
        decay_factor = self.decay_rate ** elapsed_time

        for emotion in self.emotions:
            # More intense emotions decay more slowly
            intensity_factor = 0.2 + (self.emotions[emotion] * 0.8)
            adjusted_decay = decay_factor ** intensity_factor

            # Apply decay with small random variation for more natural movement
            variation = 1.0 + random.uniform(-0.05, 0.05)  # ±5% variation
            self.emotions[emotion] *= adjusted_decay * variation

    def _apply_noise(self):
        """Apply small random changes to emotions"""
        for emotion in self.emotions:
            # Dynamic noise scale - less predictable
            intensity = self.emotions[emotion]
            base_noise = self.noise_magnitude * (1.0 - intensity * 0.7)  # Less reduction at high intensity

            # Random fluctuation in noise amount
            noise_scale = base_noise * random.uniform(0.5, 1.5)

            # Apply noise
            noise = random.uniform(-noise_scale, noise_scale)
            self.emotions[emotion] = max(0.0, min(1.0, self.emotions[emotion] + noise))

    def _apply_micro_fluctuations(self):
        """Apply tiny fluctuations to create more natural emotion movement"""
        # Pick 2-3 random emotions to adjust
        emotions_to_adjust = random.sample(list(self.emotions.keys()), random.randint(2, 3))

        for emotion in emotions_to_adjust:
            # Very small adjustments
            micro_change = random.uniform(-0.03, 0.03)

            # Apply with preference toward the middle range (more movement in neutral states)
            distance_from_mid = abs(self.emotions[emotion] - 0.5)
            if distance_from_mid > 0.3:  # Emotions far from neutral move less
                micro_change *= (1.0 - distance_from_mid)

            # Apply the micro-fluctuation
            self.emotions[emotion] = max(0.0, min(1.0, self.emotions[emotion] + micro_change))

    def _generate_thought(self, timestamp):
        """Generate a background thought using OpenAI API"""
        # Format current time
        time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')

        # Format emotions for the prompt
        emotion_text = ", ".join([f"{emotion}: {value:.2f}" for emotion, value in self.emotions.items()])

        # Get recent conversation for context
        recent_messages = self.conversation[-3:] if self.conversation else []
        context = "\n".join(recent_messages)

        try:
            # Check if we have related memories to include
            memory_context = ""
            if self.conversation:
                latest_conversation = self.conversation[-1]
                related_memories = self.memory_system.find_related_memories(latest_conversation)
                if related_memories:
                    memory_texts = [mem[0]['text'][:100] + "..." for mem in related_memories[:1]]
                    memory_context = "Related memory: " + memory_texts[0]

            # Call OpenAI API to generate a thought
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You generate brief, natural thoughts for an AI assistant based on its current emotional state and conversation context. Generate only the thought itself, no explanations or additional text."},
                    {"role": "user", "content": f"""
Current time: {time_str}
Emotional state: {emotion_text}
{memory_context}

Recent conversation:
{context}

Generate a single brief, natural thought (1-2 sentences) that might occur to an AI assistant in this moment.
                    """}
                ],
                max_tokens=60,
                temperature=0.7
            )

            thought = response.choices[0].message.content.strip()

            # Record the thought
            thought_obj = {
                "text": thought,
                "time": timestamp,
                "formatted_time": datetime.fromtimestamp(timestamp).strftime('%H:%M:%S'),
                "emotions": self.emotions.copy()
            }

            self.thoughts.append(thought_obj)

            # Keep only recent thoughts
            if len(self.thoughts) > 10:
                self.thoughts = self.thoughts[-10:]

            # Update emotions based on thought (using OpenAI again)
            self._analyze_thought_impact(thought)

        except Exception as e:
            print(f"Error generating thought: {e}")

    def _analyze_thought_impact(self, thought):
        """Analyze emotional impact of a thought using OpenAI API"""
        try:
            # Call OpenAI to analyze emotional impact
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You analyze how a thought would impact emotions. You return a JSON object with emotion names as keys and values from -0.2 to 0.2 indicating how much each emotion should change."},
                    {"role": "user", "content": f"Analyze the emotional impact of this thought: '{thought}'. Return a JSON object with these emotions: joy, sadness, anger, fear, surprise, trust, disgust, anticipation. Values should be from -0.2 to 0.2."}
                ],
                max_tokens=150,
                temperature=0.3
            )

            # Extract JSON from response
            analysis_text = response.choices[0].message.content.strip()
            try:
                # Extract JSON if it's wrapped in backticks or has explanatory text
                if "```json" in analysis_text:
                    json_str = analysis_text.split("```json")[1].split("```")[0].strip()
                elif "```" in analysis_text:
                    json_str = analysis_text.split("```")[1].strip()
                else:
                    json_str = analysis_text

                impact = json.loads(json_str)

                # Update emotions based on the analysis
                for emotion, change in impact.items():
                    if emotion in self.emotions:
                        self.emotions[emotion] = max(0.0, min(1.0, self.emotions[emotion] + float(change)))

            except json.JSONDecodeError:
                print(f"Error parsing emotional impact: {analysis_text}")

        except Exception as e:
            print(f"Error analyzing thought impact: {e}")

    def process_message(self, message):
        """Process a user message, update emotions, and generate a response

        Args:
            message: User message text

        Returns:
            str: Generated response
        """
        # Update last interaction time
        self.last_interaction = time.time()

        # Add to conversation history
        self.conversation.append(f"User: {message}")

        try:
            # Check for emotional memories that might be triggered
            memory_influences = {}
            if self.memory_system:
                related_emotional = self.memory_system.find_emotional_memories(message)
                for memory, similarity in related_emotional:
                    if memory.get("emotions"):
                        influence_strength = similarity * 0.3  # Scale by similarity
                        for emotion, value in memory["emotions"].items():
                            deviation = (value - 0.5) * influence_strength
                            if emotion in memory_influences:
                                memory_influences[emotion] += deviation
                            else:
                                memory_influences[emotion] = deviation

            # Analyze message for direct emotional impact
            direct_impacts = self._analyze_message_impact(message)

            # Apply combined emotional impacts (memory has 30% weight)
            combined_impacts = {}
            for emotion in self.emotions:
                direct = direct_impacts.get(emotion, 0) if isinstance(direct_impacts, dict) else 0
                memory = memory_influences.get(emotion, 0)
                combined_impacts[emotion] = (direct * 0.7) + (memory * 0.3)

                # Apply significant emotional changes
                if abs(combined_impacts[emotion]) > 0.01:
                    self.emotions[emotion] = max(0.0, min(1.0, self.emotions[emotion] + combined_impacts[emotion]))

            # Generate response using OpenAI
            response = self._generate_response(message)

            # Add response to conversation
            self.conversation.append(f"AI: {response}")

            # Store this interaction in memory
            conversation_text = f"User: {message}\nAI: {response}"
            self.memory_system.add_memory(
                conversation_text,
                source="conversation",
                emotions=self.emotions.copy()
            )

            # Keep conversation history manageable
            if len(self.conversation) > 20:
                self.conversation = self.conversation[-20:]

            return response

        except Exception as e:
            print(f"Error processing message: {e}")
            return "I'm sorry, I encountered an error processing your message."

    def _analyze_message_impact(self, message):
        """Analyze emotional impact of user message using OpenAI API

        Args:
            message: User message text

        Returns:
            dict: Emotional impacts
        """
        try:
            # Call OpenAI to analyze emotional impact
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You analyze how a message would impact emotions. You return a JSON object with emotion names as keys and values from -0.2 to 0.2 indicating how much each emotion should change."},
                    {"role": "user", "content": f"Analyze the emotional impact of this message: '{message}'. Return a JSON object with these emotions: joy, sadness, anger, fear, surprise, trust, disgust, anticipation. Values should be from -0.2 to 0.2."}
                ],
                max_tokens=150,
                temperature=0.3
            )

            # Extract JSON from response
            analysis_text = response.choices[0].message.content.strip()
            try:
                # Extract JSON if it's wrapped in backticks or has explanatory text
                if "```json" in analysis_text:
                    json_str = analysis_text.split("```json")[1].split("```")[0].strip()
                elif "```" in analysis_text:
                    json_str = analysis_text.split("```")[1].strip()
                else:
                    json_str = analysis_text

                impact = json.loads(json_str)
                return impact

            except json.JSONDecodeError:
                print(f"Error parsing emotional impact: {analysis_text}")
                return {}

        except Exception as e:
            print(f"Error analyzing message impact: {e}")
            return {}

    def _generate_response(self, message):
        """Generate a response using OpenAI that takes into account emotional state

        Args:
            message: User message text

        Returns:
            str: Generated response
        """
        # Format emotions for the prompt
        emotion_text = ", ".join([f"{emotion}: {value:.2f}" for emotion, value in self.emotions.items()])

        # Get recent thoughts
        recent_thoughts = [t["text"] for t in self.thoughts[-3:]] if self.thoughts else []
        thoughts_text = "\n".join([f"- {t}" for t in recent_thoughts])

        # Find related memories to include in context
        memory_context = ""
        if self.memory_system:
            related_memories = self.memory_system.find_related_memories(message)
            if related_memories:
                memory_texts = [f"- {mem[0]['text'][:100]}..." for mem in related_memories]
                memory_context = "Related memories:\n" + "\n".join(memory_texts)

        # Get recent conversation
        recent_messages = self.conversation[-6:] if self.conversation else []
        context = "\n".join(recent_messages)

        try:
            # Call OpenAI API to generate response
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"""You are an AI assistant with an emotional state that influences your responses.

Current emotional state:
{emotion_text}

Recent background thoughts:
{thoughts_text}

{memory_context}

Your response should be influenced by your current emotional state and memories, but you should not explicitly mention your emotions unless directly asked about them. The emotional influence should be subtle and natural, affecting your tone, word choice, and perspective.
                    """},
                    {"role": "user", "content": message}
                ],
                max_tokens=250,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm sorry, I encountered an error generating a response."

    def get_state(self):
        """Get the current emotional state for display in UI

        Returns:
            dict: Current emotional state
        """
        return {
            "emotions": self.emotions,
            "thoughts": self.thoughts,
            "history": self.emotion_history
        }

    def reset(self):
        """Reset the emotional system state"""
        for emotion in self.emotions:
            self.emotions[emotion] = 0.0
        self.thoughts = []
        self.emotion_history = [self.emotions.copy()]
        # Keep conversation history

    def stop(self):
        """Stop the background thread"""
        self.running = False
        if self.background_thread.is_alive():
            self.background_thread.join(timeout=1.0)