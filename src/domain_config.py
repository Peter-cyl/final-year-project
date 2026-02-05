"""
Domain Configuration Module
Provides multi-domain support through configuration profiles.

This module externalizes domain-specific mappings that were previously
hard-coded, allowing the system to work with multiple planning domains.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class DomainProfile:
    """
    Configuration profile for a specific planning domain.

    Contains all domain-specific mappings needed for natural language generation:
    - Object name mappings (technical IDs to readable names)
    - Location name mappings
    - Type labels
    - Predicate and action descriptions
    """
    domain_name: str
    description: str

    # Object name mappings: {"t1": "Truck 1", "d1": "Driver Dave"}
    object_names: Dict[str, str] = field(default_factory=dict)

    # Location name mappings: {"a": "Depot", "b": "Butcher"}
    location_names: Dict[str, str] = field(default_factory=dict)

    # Type labels for natural language: {"truck": "the truck", "driver": "the driver"}
    type_labels: Dict[str, str] = field(default_factory=dict)

    # Predicate descriptions (overrides PDDL comments if provided)
    # Format: {"predicate_name": "description with {0}, {1} for parameters"}
    predicate_descriptions: Dict[str, str] = field(default_factory=dict)

    # Action descriptions (overrides PDDL comments if provided)
    action_descriptions: Dict[str, str] = field(default_factory=dict)

    # Templates for different verbalization contexts
    templates: Dict[str, str] = field(default_factory=dict)

    def get_object_label(self, obj_id: str) -> str:
        """Get human-readable label for an object."""
        return self.object_names.get(obj_id, obj_id.upper())

    def get_location_label(self, loc_id: str) -> str:
        """Get human-readable label for a location."""
        return self.location_names.get(loc_id, loc_id.upper())

    def get_type_label(self, type_name: str) -> str:
        """Get human-readable label for a type."""
        return self.type_labels.get(type_name, type_name)

    def get_readable_value(self, value: str) -> str:
        """Get human-readable version of any value (object, location, or as-is)."""
        if value in self.object_names:
            return self.object_names[value]
        if value in self.location_names:
            return self.location_names[value]
        return value.upper() if value.islower() and len(value) <= 3 else value


class DomainConfigManager:
    """
    Manages domain configuration profiles.

    Provides built-in profiles for the 5 required domains and supports
    loading custom profiles from JSON files.
    """

    DEFAULT_CONFIG_DIR = "config/domains"

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else None
        self.profiles: Dict[str, DomainProfile] = {}
        self._load_builtin_profiles()

        # Try to load from config directory if it exists
        if self.config_dir and self.config_dir.exists():
            self._load_profiles_from_dir()

    def _load_builtin_profiles(self):
        """Load built-in domain profiles for all required domains."""
        self.profiles["refrigerated_delivery"] = self._refrigeration_profile()
        self.profiles["rover"] = self._rover_profile()
        self.profiles["satellite"] = self._satellite_profile()
        self.profiles["settlers"] = self._settlers_profile()
        self.profiles["crewplanning"] = self._crewplanning_profile()

    def _refrigeration_profile(self) -> DomainProfile:
        """Profile for the refrigerated delivery domain."""
        return DomainProfile(
            domain_name="refrigerated_delivery",
            description="Refrigerated produce delivery with trucks and drivers. "
                       "Manages time-sensitive deliveries where certain products "
                       "require refrigeration to remain fresh.",
            object_names={
                "t1": "Truck 1", "t2": "Truck 2",
                "d1": "Driver 1", "d2": "Driver 2",
                "m": "the meat", "ce": "the cereal",
                "p1": "Product 1", "p2": "Product 2"
            },
            location_names={
                "a": "Depot", "b": "Butcher", "c": "Grocer",
                "depot": "Depot", "butcher": "Butcher", "grocer": "Grocer"
            },
            type_labels={
                "truck": "the truck",
                "driver": "the driver",
                "meat": "the meat",
                "cereal": "the cereal",
                "prod": "the produce",
                "location": "the location",
                "locatable": "the item"
            },
            predicate_descriptions={
                "refrigerated": "{0} is refrigerated",
                "can_deliver": "{0} can be delivered (is still fresh)",
                "boarded": "{0} has boarded {1}",
                "in": "{0} is loaded in {1}",
                "at": "{0} is at {1}"
            },
            action_descriptions={
                "load_truck": "Load {0} into truck {1} at {2}",
                "board_truck": "Driver {0} boards truck {1} at {2}",
                "drive_truck": "Driver {0} drives truck {1} from {2} to {3}",
                "deliver_produce": "Deliver {0} from truck {1} to {2}",
                "extend_meat_life": "Keep the meat fresh in refrigerated truck {0}"
            },
            templates={
                "predicate": "If we did not require that {precondition_desc} in order to {action_desc}, then we could:",
                "duration": "If {action_desc} took {new_duration} instead of {old_duration}, then we could:",
                "til": "If {fact_desc} did not become {state} at time {time}, then we could:"
            }
        )

    def _rover_profile(self) -> DomainProfile:
        """Profile for the Mars rover exploration domain."""
        return DomainProfile(
            domain_name="rover",
            description="Mars rover exploration and sample collection. "
                       "Rovers navigate waypoints, collect soil/rock samples, "
                       "and communicate data back to Earth via landers.",
            object_names={
                "rover0": "Rover 0", "rover1": "Rover 1",
                "general": "the general store",
                "colour": "the colour camera",
                "high_res": "the high-resolution camera",
                "low_res": "the low-resolution camera"
            },
            location_names={
                "waypoint0": "Waypoint 0", "waypoint1": "Waypoint 1",
                "waypoint2": "Waypoint 2", "waypoint3": "Waypoint 3"
            },
            type_labels={
                "rover": "the rover",
                "waypoint": "the waypoint",
                "store": "the storage",
                "camera": "the camera",
                "mode": "the mode",
                "lander": "the lander",
                "objective": "the objective"
            },
            predicate_descriptions={
                "at": "{0} is at {1}",
                "at_lander": "{0} is at lander {1}",
                "can_traverse": "{0} can traverse from {1} to {2}",
                "equipped_for_soil_analysis": "{0} is equipped for soil analysis",
                "equipped_for_rock_analysis": "{0} is equipped for rock analysis",
                "equipped_for_imaging": "{0} is equipped for imaging",
                "empty": "{0} is empty",
                "have_rock_analysis": "{0} has rock analysis data from {1}",
                "have_soil_analysis": "{0} has soil analysis data from {1}",
                "full": "{0} is full",
                "calibrated": "{0} is calibrated for {1}",
                "supports": "{0} supports {1}",
                "available": "{0} is available",
                "visible": "{0} is visible from {1}",
                "have_image": "{0} has image of {1} in mode {2}",
                "communicated_soil_data": "soil data from {0} has been communicated",
                "communicated_rock_data": "rock data from {0} has been communicated",
                "communicated_image_data": "image of {0} in mode {1} has been communicated",
                "at_soil_sample": "there is a soil sample at {0}",
                "at_rock_sample": "there is a rock sample at {0}",
                "visible_from": "{0} is visible from {1}",
                "store_of": "{0} is the store of {1}",
                "calibration_target": "{0} is the calibration target for {1}",
                "on_board": "{0} is on board {1}",
                "channel_free": "{0} has a free channel",
                "in_sun": "{0} is in sunlight",
                "energy": "{0} has energy level {1}"
            },
            action_descriptions={
                "navigate": "Rover {0} navigates from {1} to {2}",
                "sample_soil": "Rover {0} samples soil at {2} using store {1}",
                "sample_rock": "Rover {0} samples rock at {2} using store {1}",
                "drop": "Rover {0} empties store {1}",
                "calibrate": "Rover {0} calibrates camera {1} at {2} using target {3}",
                "take_image": "Rover {0} takes image of {2} in mode {3} at {4}",
                "communicate_soil_data": "Rover {0} communicates soil data from {2} to lander {1}",
                "communicate_rock_data": "Rover {0} communicates rock data from {2} to lander {1}",
                "communicate_image_data": "Rover {0} communicates image of {2} to lander {1}"
            }
        )

    def _satellite_profile(self) -> DomainProfile:
        """Profile for the satellite observation domain."""
        return DomainProfile(
            domain_name="satellite",
            description="Satellite observation scheduling. Satellites must point "
                       "instruments at targets, calibrate them, and capture images "
                       "in various modes.",
            object_names={
                "satellite0": "Satellite 0", "satellite1": "Satellite 1",
                "instrument0": "Instrument 0", "instrument1": "Instrument 1"
            },
            location_names={
                "groundstation0": "Ground Station 0",
                "groundstation1": "Ground Station 1"
            },
            type_labels={
                "satellite": "the satellite",
                "direction": "the direction",
                "instrument": "the instrument",
                "mode": "the mode",
                "calib_direction": "the calibration direction"
            },
            predicate_descriptions={
                "on_board": "{0} is on board {1}",
                "supports": "{0} supports mode {1}",
                "pointing": "{0} is pointing at {1}",
                "power_avail": "{0} has power available",
                "power_on": "{0} is powered on",
                "calibrated": "{0} is calibrated",
                "have_image": "image of {0} in mode {1} has been taken",
                "calibration_target": "{0} is calibrated for direction {1}"
            },
            action_descriptions={
                "turn_to": "Turn {0} from {2} to {1}",
                "switch_on": "Switch on {0} on satellite {1}",
                "switch_off": "Switch off {0} on satellite {1}",
                "calibrate": "Calibrate {0} on {1} pointing at {2}",
                "take_image": "Take image of {1} in mode {2} using {0} on {3}"
            }
        )

    def _settlers_profile(self) -> DomainProfile:
        """Profile for the settlers/colony building domain."""
        return DomainProfile(
            domain_name="settlers",
            description="Colony building and resource management. Build infrastructure "
                       "like rails and housing, manage resources and labor to establish "
                       "a settlement.",
            object_names={},
            location_names={
                "place0": "Place 0", "place1": "Place 1",
                "place2": "Place 2", "place3": "Place 3"
            },
            type_labels={
                "place": "the place",
                "vehicle": "the vehicle",
                "resource": "the resource",
                "labour": "the labour",
                "housing": "the housing"
            },
            predicate_descriptions={
                "connected-by-rail": "{0} is connected by rail to {1}",
                "connected-by-land": "{0} is connected by land to {1}",
                "available": "{0} is available at {1}",
                "potential": "{0} has potential for {1}",
                "stored": "{0} has {1} stored at {2}",
                "space-in-train": "the train at {0} has space for {1}",
                "has-cabin": "{0} has a cabin",
                "has-coal-stack": "{0} has a coal stack",
                "has-docks": "{0} has docks",
                "has-wharf": "{0} has a wharf",
                "has-sawmill": "{0} has a sawmill",
                "has-ironworks": "{0} has ironworks",
                "has-quarry": "{0} has a quarry",
                "housing": "{0} has housing level {1}"
            },
            action_descriptions={
                "build-rail": "Build rail from {0} to {1}",
                "build-train": "Build train at {0}",
                "load-train": "Load {2} onto train at {0} from {1}",
                "unload-train": "Unload {2} from train at {0} to {1}",
                "move-train": "Move train from {0} to {1}"
            }
        )

    def _crewplanning_profile(self) -> DomainProfile:
        """Profile for the crew planning domain."""
        return DomainProfile(
            domain_name="crewplanning",
            description="Crew scheduling and task planning. Manage crew members' "
                       "activities including meals, rest, exercises, and mission tasks "
                       "across multiple days.",
            object_names={
                "c1": "Crew Member 1", "c2": "Crew Member 2",
                "c3": "Crew Member 3"
            },
            location_names={},
            type_labels={
                "crew_member": "the crew member",
                "day": "the day",
                "meal": "the meal",
                "exercise": "the exercise"
            },
            predicate_descriptions={
                "available": "{0} is available on {1}",
                "done_meal": "{0} has completed meal {1} on {2}",
                "done_sleep": "{0} has slept on {1}",
                "done_exercise": "{0} has exercised ({1}) on {2}",
                "done_mcs": "{0} has completed MCS on {1}",
                "done_rpcm": "{0} has completed RPCM on {1}",
                "initiated": "day {0} has been initiated",
                "next": "{0} follows {1}"
            },
            action_descriptions={
                "do_meal": "{0} eats meal {1} on {2}",
                "do_sleep": "{0} sleeps on {1}",
                "do_exercise": "{0} exercises ({1}) on {2}",
                "do_mcs": "{0} performs MCS on {1}",
                "do_rpcm": "{0} performs RPCM on {1}",
                "initiate_day": "Initiate day {0} after {1}"
            }
        )

    def get_profile(self, domain_name: str) -> Optional[DomainProfile]:
        """
        Get profile by domain name (case-insensitive, partial matching).

        Args:
            domain_name: Name of the domain to look up

        Returns:
            DomainProfile if found, None otherwise
        """
        # Try exact match first
        name_lower = domain_name.lower().replace('-', '_').replace(' ', '_')
        if name_lower in self.profiles:
            return self.profiles[name_lower]

        # Try partial match
        for key, profile in self.profiles.items():
            if key in name_lower or name_lower in key:
                return profile

        return None

    def get_profile_for_domain(self, domain_name: str) -> DomainProfile:
        """
        Get profile for domain, creating a default if not found.

        Args:
            domain_name: Name of the domain

        Returns:
            DomainProfile (existing or default)
        """
        profile = self.get_profile(domain_name)
        if profile:
            return profile

        # Create a default profile
        return DomainProfile(
            domain_name=domain_name,
            description=f"Planning domain: {domain_name}"
        )

    def list_profiles(self) -> List[str]:
        """List all available profile names."""
        return list(self.profiles.keys())

    def _load_profiles_from_dir(self):
        """Load profiles from JSON files in config directory."""
        if not self.config_dir:
            return

        for json_file in self.config_dir.glob("*.json"):
            try:
                profile = self.load_profile_from_file(str(json_file))
                self.profiles[profile.domain_name.lower()] = profile
            except Exception as e:
                print(f"Warning: Failed to load profile from {json_file}: {e}")

    def load_profile_from_file(self, filepath: str) -> DomainProfile:
        """
        Load a profile from a JSON configuration file.

        Args:
            filepath: Path to JSON file

        Returns:
            Loaded DomainProfile
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        profile = DomainProfile(
            domain_name=data.get('domain_name', 'unknown'),
            description=data.get('description', ''),
            object_names=data.get('object_names', {}),
            location_names=data.get('location_names', {}),
            type_labels=data.get('type_labels', {}),
            predicate_descriptions=data.get('predicate_descriptions', {}),
            action_descriptions=data.get('action_descriptions', {}),
            templates=data.get('templates', {})
        )

        return profile

    def save_profile_to_file(self, profile: DomainProfile, filepath: str):
        """
        Save a profile to a JSON file.

        Args:
            profile: Profile to save
            filepath: Destination path
        """
        with open(filepath, 'w') as f:
            json.dump(asdict(profile), f, indent=2)


# Test code
if __name__ == "__main__":
    manager = DomainConfigManager()

    print("Available profiles:", manager.list_profiles())

    # Test refrigeration profile
    profile = manager.get_profile("refrigerated_delivery")
    if profile:
        print(f"\nProfile: {profile.domain_name}")
        print(f"Description: {profile.description}")
        print(f"Object 't1': {profile.get_object_label('t1')}")
        print(f"Location 'a': {profile.get_location_label('a')}")
        print(f"Type 'truck': {profile.get_type_label('truck')}")

    # Test rover profile
    profile = manager.get_profile("rover")
    if profile:
        print(f"\nProfile: {profile.domain_name}")
        print(f"Description: {profile.description}")
