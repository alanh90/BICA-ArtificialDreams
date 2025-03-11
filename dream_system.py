import threading
import time
import random
import json
from datetime import datetime
import numpy as np


class DreamSystem:
    def __init__(self, client, memory_system):
        """Initialize the Dream System

        Args:
            client: OpenAI client for generating dreams and scenarios
            memory_system: Reference to the MemorySystem for accessing and updating memories
        """
        self.client = client
        self.memory_system = memory_system

        # Dream state and records
        self.current_dream = None
        self.dream_records = []
        self.consolidated_memories = []
        self.hypothetical_scenarios = []
        self.dream_insights = []

        # Configuration parameters
        self.dream_frequency = 60  # How often to dream (in seconds)
        self.dream_duration = 30  # How long a dream cycle lasts (in seconds)
        self.consolidation_threshold = 0.4  # Memories below this importance are consolidated
        self.dreaming = False
        self.current_stage = "idle"

        # Optimization parameters
        self.diminishing_returns_threshold = 0.3  # Threshold for early termination
        self.early_termination_enabled = True  # Whether to enable early termination
        self.last_optimization_value = 0  # Track last optimization value

        # Background thread control
        self.running = False
        self.auto_dreaming_enabled = False  # Disable auto-dreaming by default
        self.background_thread = None
        self.last_dream_time = 0

    def start(self):
        """Start the background monitoring thread"""
        if not self.running:
            self.running = True
            self.background_thread = threading.Thread(target=self._background_process)
            self.background_thread.daemon = True
            self.background_thread.start()
            print("Dream system started (monitoring only)")

    def stop(self):
        """Stop the background monitoring thread"""
        self.running = False
        if self.background_thread and self.background_thread.is_alive():
            self.background_thread.join(timeout=2.0)
            print("Dream system stopped")

    def _background_process(self):
        """Background process for monitoring but not automatically triggering dreams"""
        while self.running:
            # This thread now only monitors the system and doesn't auto-trigger dreams
            # It could still update UI elements or perform other monitoring tasks

            # For example, it could update the count of unprocessed memories for display
            unprocessed_count = len(self.memory_system.get_unprocessed_memories())
            if unprocessed_count > 15:
                print(f"System has {unprocessed_count} unprocessed memories ready for dreaming")

            # Sleep for a while before checking again
            time.sleep(5)

    def trigger_dream_cycle(self):
        """Manually trigger a dream cycle

        Returns:
            dict: Summary of dream cycle
        """
        print("Dream cycle manually triggered")
        return self._dream_cycle()

    def _calculate_optimization_value(self, stage_data):
        """Calculate a value to determine if dreaming should continue

        Args:
            stage_data: Data about the current dream stage

        Returns:
            float: Optimization value between 0-1
        """
        # This is a simple optimization function that could be enhanced
        # It returns higher values when dreaming is still productive

        if not stage_data:
            return 0.5  # Default middle value if no data

        # Factors to consider:
        # 1. How many memories were processed in this stage
        # 2. How significant the results were (quality of consolidations/insights)
        # 3. How many unprocessed memories remain

        # For consolidation stage:
        if self.current_stage == "consolidation":
            if "consolidations" in stage_data:
                # More consolidations = higher value
                consolidation_count = len(stage_data["consolidations"])
                # Diminishing returns: more value for first few consolidations
                consolidation_factor = min(1.0, consolidation_count / 5.0)
                return consolidation_factor

        # For hypothesis stage:
        elif self.current_stage == "hypothesis":
            if "scenarios" in stage_data:
                # More varied scenarios = higher value
                scenario_count = len(stage_data["scenarios"])
                scenario_factor = min(1.0, scenario_count / 4.0)

                # Consider scenario quality (probability)
                avg_probability = 0.5
                if scenario_count > 0:
                    avg_probability = sum(s.get("probability", 0.5) for s in stage_data["scenarios"]) / scenario_count

                return 0.7 * scenario_factor + 0.3 * avg_probability

        # For insight stage:
        elif self.current_stage == "insight":
            if "insights" in stage_data:
                # More valuable insights = higher value
                insight_count = len(stage_data["insights"])
                if insight_count == 0:
                    return 0.1  # Few insights = low value in continuing

                # Consider insight quality/value
                avg_value = 0.5
                if insight_count > 0:
                    avg_value = sum(i.get("value", 0.5) for i in stage_data["insights"]) / insight_count

                return 0.4 * min(1.0, insight_count / 3.0) + 0.6 * avg_value

        # Memory selection stage - value based on available memories
        elif self.current_stage == "memory-selection":
            unprocessed_count = len(self.memory_system.get_unprocessed_memories())
            # If we have many unprocessed memories, high value in continuing
            return min(1.0, unprocessed_count / 10.0)

        # Default fallback
        return 0.5

    def _should_continue_dreaming(self, stage_data):
        """Determine if dreaming should continue based on optimization

        Args:
            stage_data: Data about the current dream stage

        Returns:
            bool: Whether to continue dreaming
        """
        if not self.early_termination_enabled:
            return True  # Always continue if optimization is disabled

        # Calculate current optimization value
        current_value = self._calculate_optimization_value(stage_data)

        # Marginal benefit is difference from last value
        marginal_benefit = current_value - self.last_optimization_value

        # Update for next iteration
        self.last_optimization_value = current_value

        # Low marginal benefit or low absolute value = stop dreaming
        if marginal_benefit < 0:  # Declining benefit
            print(f"Stopping dream early: Declining benefit (change: {marginal_benefit:.2f})")
            return False

        if current_value < self.diminishing_returns_threshold:
            print(f"Stopping dream early: Low value ({current_value:.2f} < {self.diminishing_returns_threshold})")
            return False

        return True

    def _dream_cycle(self):
        """Run a complete dream cycle

        A dream cycle consists of:
        1. Memory consolidation - combining similar low-importance memories
        2. Hypothetical scenario generation - exploring "what-if" scenarios
        3. Insight generation - drawing conclusions from scenarios
        4. Memory update - storing insights and consolidated memories

        Returns:
            dict: Summary of the dream cycle
        """
        if self.dreaming:
            return {"status": "already_dreaming", "message": "Dream cycle already in progress"}

        try:
            print("Starting dream cycle")
            self.dreaming = True
            cycle_start_time = time.time()
            self.current_dream = {
                "id": len(self.dream_records) + 1,
                "timestamp": cycle_start_time,
                "formatted_time": datetime.fromtimestamp(cycle_start_time).strftime('%Y-%m-%d %H:%M:%S'),
                "stages": [],
                "consolidations": [],
                "scenarios": [],
                "insights": []
            }

            # Reset optimization tracking
            self.last_optimization_value = 0

            # Stage 1: Memory Importance Assessment & Consolidation
            self._update_dream_stage("memory-selection")
            print("Memory selection stage started")
            time.sleep(5)  # Simulate processing time for UI visualization

            # Get memories below the consolidation threshold
            memories_to_consolidate = self.memory_system.get_memories_by_importance(
                max_importance=self.consolidation_threshold,
                min_count=3
            )

            # Also look for similar memory content
            similar_memories = self.memory_system.find_similar_memories()
            for group in similar_memories:
                memories_to_consolidate.extend(group)

            # Remove duplicates
            unique_ids = set()
            filtered_memories = []
            for memory in memories_to_consolidate:
                if memory.get("id") not in unique_ids:
                    filtered_memories.append(memory)
                    unique_ids.add(memory.get("id"))

            memories_to_consolidate = filtered_memories

            # Check optimization after memory selection
            stage_data = {"memory_count": len(memories_to_consolidate)}
            if not self._should_continue_dreaming(stage_data):
                raise Exception("Dream cycle terminated early: Not enough valuable memories to consolidate")

            if memories_to_consolidate:
                self._update_dream_stage("consolidation")
                print("Consolidation stage started")
                time.sleep(5)  # Simulate processing time for UI visualization

                consolidated = self._consolidate_memories(memories_to_consolidate)
                self.current_dream["consolidations"] = consolidated

                # Check optimization after consolidation
                stage_data = {"consolidations": consolidated}
                if not self._should_continue_dreaming(stage_data):
                    # End dream early but still save what we've done
                    print("Dream cycle ending early after consolidation due to optimization")
                    return self._finalize_dream(cycle_start_time)
            else:
                self._update_dream_stage("memory-selection")
                self.current_dream["stages"].append({
                    "description": "No memories found for consolidation",
                    "timestamp": time.time()
                })

            # Stage 2: Hypothetical Scenario Generation
            self._update_dream_stage("hypothesis")
            print("Hypothesis generation stage started")
            time.sleep(5)  # Simulate processing time for UI visualization

            scenarios = self._generate_scenarios()
            self.current_dream["scenarios"] = scenarios

            # Check optimization after scenario generation
            stage_data = {"scenarios": scenarios}
            if not self._should_continue_dreaming(stage_data):
                # End dream early but still save what we've done
                print("Dream cycle ending early after scenario generation due to optimization")
                return self._finalize_dream(cycle_start_time)

            # Stage 3: Insight Generation
            if scenarios:
                self._update_dream_stage("insight")
                print("Insight formation stage started")
                time.sleep(5)  # Simulate processing time for UI visualization

                insights = self._generate_insights(scenarios)
                self.current_dream["insights"] = insights

                # Store valuable insights as new memories
                for insight in insights:
                    if insight.get("value", 0) > 0.6:  # Only store valuable insights
                        self.memory_system.add_insight(
                            insight["text"],
                            importance=insight["value"],
                            metadata={"dream_id": self.current_dream["id"]}
                        )

                # Check optimization after insight generation
                stage_data = {"insights": insights}
                if not self._should_continue_dreaming(stage_data):
                    print("Dream cycle completed all stages but optimization suggests no further benefit")

            # Finalize the dream record
            return self._finalize_dream(cycle_start_time)

        except Exception as e:
            print(f"Error in dream cycle: {e}")
            if self.current_dream:
                return self._finalize_dream(cycle_start_time, error=str(e))
            return {"status": "error", "message": str(e)}
        finally:
            self._update_dream_stage("idle")
            self.dreaming = False
            self.current_dream = None

    def _finalize_dream(self, start_time, error=None):
        """Finalize the dream record and return summary

        Args:
            start_time: When the dream cycle started
            error: Optional error message

        Returns:
            dict: Summary of the dream cycle
        """
        # Calculate duration
        cycle_duration = time.time() - start_time
        self.current_dream["duration"] = cycle_duration

        # Add early termination info if applicable
        if error:
            self.current_dream["early_termination"] = True
            self.current_dream["termination_reason"] = error

        # Save the dream record
        self.dream_records.append(self.current_dream)
        print(f"Dream cycle completed in {cycle_duration:.2f} seconds")

        # Keep only recent dream records in memory
        if len(self.dream_records) > 10:
            self.dream_records = self.dream_records[-10:]

        # Return summary of the dream cycle
        result = {
            "dream_id": self.current_dream["id"],
            "duration": cycle_duration,
            "memories_consolidated": len(self.current_dream.get("consolidations", [])),
            "scenarios_explored": len(self.current_dream.get("scenarios", [])),
            "insights_generated": len(self.current_dream.get("insights", [])),
            "early_termination": "early_termination" in self.current_dream
        }

        if "early_termination" in self.current_dream:
            result["termination_reason"] = self.current_dream.get("termination_reason", "Optimization-based early termination")

        return result

    def _update_dream_stage(self, stage_description):
        """Update the current stage of dreaming"""
        print(f"Updating dream stage to: {stage_description}")
        self.current_stage = stage_description

        if self.current_dream:
            self.current_dream["stages"].append({
                "description": stage_description,
                "timestamp": time.time()
            })

    def _consolidate_memories(self, memories):
        """Consolidate similar low-importance memories

        Args:
            memories: List of memories to consolidate

        Returns:
            list: List of consolidation records
        """
        consolidations = []

        # Group memories by similarity
        # First, group memories that have the same similar_to metadata value
        grouped_memories = {}
        standalone_memories = []

        for memory in memories:
            metadata = memory.get("metadata", {})
            similar_to = metadata.get("similar_to")

            if similar_to:
                # Create a key based on the similar_to ID
                if similar_to not in grouped_memories:
                    grouped_memories[similar_to] = []
                grouped_memories[similar_to].append(memory)
            else:
                # For memories without similar_to tag, group by event_type
                if "event_type" in metadata:
                    event_type = metadata["event_type"]
                    key = f"type_{event_type}"
                    if key not in grouped_memories:
                        grouped_memories[key] = []
                    grouped_memories[key].append(memory)
                else:
                    standalone_memories.append(memory)

        # Process each group
        for key, memory_group in grouped_memories.items():
            if len(memory_group) < 2:
                continue  # Need at least 2 memories to consolidate

            try:
                # Use OpenAI to generate a consolidation
                memory_texts = [f"- {m['text']}" for m in memory_group[:5]]
                prompt = f"""
                Consolidate these similar memories into a single concise memory that captures their essence:

                {chr(10).join(memory_texts)}

                Think about how human memory works: when we experience similar events multiple times, 
                we often merge them into one generalized memory with key details preserved.

                Return only the consolidated memory text, no explanations.
                """

                if not self.client:
                    print("OpenAI client not available, using simple consolidation")
                    consolidated_text = f"Combined memory from {len(memory_group)} similar events: {memory_group[0]['text']}"
                else:
                    print(f"Generating consolidated memory for {len(memory_group)} memories")
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You consolidate similar memories into a single memory that captures their essence, similar to how human memory works during sleep."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=150,
                        temperature=0.3
                    )

                    consolidated_text = response.choices[0].message.content.strip()

                # Calculate average importance and create the consolidated memory
                avg_importance = sum(m.get("importance", 0.2) for m in memory_group) / len(memory_group)

                # Get metadata for the consolidated memory (preserve event_type)
                consolidated_metadata = {
                    "dream_id": self.current_dream["id"],
                    "original_count": len(memory_group),
                    "consolidated_from": [m.get("id") for m in memory_group]
                }

                # Preserve the event_type if all memories have the same type
                event_types = set()
                for m in memory_group:
                    if m.get("metadata") and "event_type" in m.get("metadata", {}):
                        event_types.add(m["metadata"]["event_type"])

                if len(event_types) == 1:
                    consolidated_metadata["event_type"] = list(event_types)[0]

                # Store the consolidated memory
                self.memory_system.add_consolidated_memory(
                    consolidated_text,
                    importance=min(avg_importance * 1.2, 0.8),  # Give a slight boost but cap it
                    metadata=consolidated_metadata
                )

                # Mark original memories as processed
                memory_ids = [m.get("id") for m in memory_group]
                self.memory_system.mark_memories_processed(memory_ids)

                # Record the consolidation
                consolidations.append({
                    "original_memories": [m["text"] for m in memory_group],
                    "consolidated_text": consolidated_text,
                    "source": memory_group[0].get("source", "unknown"),
                    "count": len(memory_group)
                })

                print(f"Successfully consolidated {len(memory_group)} memories")

            except Exception as e:
                print(f"Error consolidating memories: {e}")

        return consolidations

    def _generate_scenarios(self):
        """Generate hypothetical scenarios based on memories and current state

        Returns:
            list: Generated hypothetical scenarios
        """
        scenarios = []

        # Get important memories for context
        important_memories = self.memory_system.get_memories_by_importance(min_importance=0.7, max_count=3)
        recent_memories = self.memory_system.get_recent_memories(max_count=3)

        # Combine important and recent memories, removing duplicates
        context_memories = []
        seen_ids = set()
        for memory in important_memories + recent_memories:
            if memory.get("id") not in seen_ids:
                context_memories.append(memory)
                seen_ids.add(memory.get("id"))

        # If we have context memories, generate scenarios
        if not context_memories:
            print("No context memories found for scenario generation")
            return scenarios

        try:
            # Format memories for the prompt
            memory_texts = [f"- {m['text']}" for m in context_memories[:5]]

            prompt = f"""
            Based on these memories, generate 2-3 hypothetical scenarios that could occur in the future.
            Each scenario should be a brief "what if" thought experiment relevant to the context.

            Memories:
            {chr(10).join(memory_texts)}

            Format each scenario as a JSON object with:
            1. "scenario": A brief description of the hypothetical scenario
            2. "relevance": Why this scenario is relevant to current memories (1-2 sentences)
            3. "probability": A number from 0-1 indicating how likely this scenario is

            Return a JSON array of scenario objects.
            """

            if not self.client:
                print("OpenAI client not available, using simple scenarios")
                # Create a simple scenario as fallback
                scenarios = [{
                    "scenario": "What if similar events happen again tomorrow?",
                    "relevance": "Based on the pattern of repeated events in memories",
                    "probability": 0.7,
                    "timestamp": time.time(),
                    "id": str(time.time()) + "_" + str(random.randint(1000, 9999))
                }]
            else:
                print("Generating hypothetical scenarios")
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You generate hypothetical scenarios based on provided memories."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )

                # Extract JSON from response
                content = response.choices[0].message.content.strip()

                # Handle various JSON formats that might be returned
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].strip()
                else:
                    json_str = content

                generated_scenarios = json.loads(json_str)

                # Process and enhance each scenario
                for scenario in generated_scenarios:
                    # Add timestamp and ID
                    scenario["timestamp"] = time.time()
                    scenario["id"] = str(time.time()) + "_" + str(random.randint(1000, 9999))
                    scenarios.append(scenario)

            # Store the scenarios in hypothetical_scenarios
            self.hypothetical_scenarios.extend(scenarios)

            # Keep only recent scenarios in memory
            if len(self.hypothetical_scenarios) > 15:
                self.hypothetical_scenarios = self.hypothetical_scenarios[-15:]

            print(f"Generated {len(scenarios)} hypothetical scenarios")

        except Exception as e:
            print(f"Error generating scenarios: {e}")

        return scenarios

    def _generate_insights(self, scenarios):
        """Generate insights from hypothetical scenarios

        Args:
            scenarios: List of hypothetical scenarios to analyze

        Returns:
            list: Generated insights
        """
        insights = []

        if not scenarios:
            print("No scenarios available for insight generation")
            return insights

        try:
            # Format scenarios for the prompt
            scenario_texts = [f"Scenario {i + 1}: {s['scenario']}\nRelevance: {s['relevance']}\nProbability: {s['probability']}"
                              for i, s in enumerate(scenarios)]

            prompt = f"""
            Based on these hypothetical scenarios, generate 1-2 key insights or learnings that could be valuable.
            Think about patterns, potential actions, or deeper understandings that emerge from considering these scenarios.

            Scenarios:
            {chr(10).join(scenario_texts)}

            Format each insight as a JSON object with:
            1. "text": The insight or learning (1-2 sentences)
            2. "value": A number from 0-1 indicating how valuable this insight is
            3. "application": A brief description of how this insight could be applied

            Return a JSON array of insight objects.
            """

            if not self.client:
                print("OpenAI client not available, using simple insight")
                # Create a simple insight as fallback
                insights = [{
                    "text": "Recurring patterns in daily events suggest opportunities for optimization",
                    "value": 0.75,
                    "application": "Could be applied to improve daily routines and interactions",
                    "timestamp": time.time(),
                    "id": str(time.time()) + "_" + str(random.randint(1000, 9999))
                }]
            else:
                print("Generating insights from scenarios")
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You generate valuable insights from hypothetical scenarios."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=350,
                    temperature=0.5
                )

                # Extract JSON from response
                content = response.choices[0].message.content.strip()

                # Handle various JSON formats that might be returned
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].strip()
                else:
                    json_str = content

                generated_insights = json.loads(json_str)

                # Process each insight
                for insight in generated_insights:
                    # Add timestamp and ID
                    insight["timestamp"] = time.time()
                    insight["id"] = str(time.time()) + "_" + str(random.randint(1000, 9999))
                    insights.append(insight)

            # Store the insights
            self.dream_insights.extend(insights)

            # Keep only recent insights in memory
            if len(self.dream_insights) > 15:
                self.dream_insights = self.dream_insights[-15:]

            print(f"Generated {len(insights)} insights")

        except Exception as e:
            print(f"Error generating insights: {e}")

        return insights

    def get_state(self):
        """Get the current state of the dream system for display in UI

        Returns:
            dict: Current dream system state
        """
        return {
            "dreaming": self.dreaming,
            "current_stage": self.current_stage,
            "last_dream_time": self.last_dream_time,
            "current_dream": self.current_dream,
            "consolidated_count": len(self.memory_system.get_consolidated_memories()),
            "scenarios_count": len(self.hypothetical_scenarios),
            "insights_count": len(self.memory_system.get_insights())
        }

    def get_recent_dreams(self):
        """Get recent dream records for display

        Returns:
            list: Recent dream records
        """
        return self.dream_records

    def reset(self):
        """Reset the dream system state"""
        self.current_dream = None
        self.dream_records = []
        self.hypothetical_scenarios = []
        self.dream_insights = []
        self.current_stage = "idle"
        self.dreaming = False
        self.last_dream_time = 0