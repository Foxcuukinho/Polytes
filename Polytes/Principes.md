# Polytes - Principles

## Objective/Description

Polytes is a stickman that lives on your computer. The computer is his home: windows, icons, and everything else are objects in his house that he can interact with.

His entire world is the computer: the operating system, apps, websites, files, and everything else. If it exists on the computer, it is part of his world.

He does not just react to his environment; he interacts with it and can change it. The goal is to make him feel like something truly alive inside the computer, similar to the stickmen in Alan Becker's animations.

## Pillars

These are the three pillars that guide Polytes' development. Every idea should strengthen at least one of them.

### 1. Animation and Physics

The most important pillar. Regardless of how complex his intelligence is, if his animation and physical behavior do not feel alive, Polytes will not feel alive.

- **Animation:** Defines how Polytes moves and expresses himself through movement.
    
    - **Procedural Animation:** Generates and adapts animations dynamically rather than relying entirely on predefined animation sequences.
        
    - **Rig Editor:** Allows the character's rig to be edited, providing control over its structure and movement capabilities.
        
- **Physics:** Defines how Polytes' body behaves physically and interacts with the environment.
    
    - **Ragdoll:** Simulates the movement and response of his body through connected body parts and physical forces.
        
    - **Basic Collision:** Allows Polytes to detect and respond to collisions with surfaces and other objects.
        

### 2. Intelligence

Defines Polytes' individual characteristics, internal motivations, and behavior choices.

- **Personality:** Defines who Polytes is through attributes that influence his behavior and decisions. In V1, these traits are generated from his name, color, and head type. Whether they can change over time is still undecided.
    
- **Needs:** Represents Polytes' internal needs, which influence his behavior and decisions. In V1, needs such as stamina and boredom already affect his behavior.
    
- **Decision:** Determines what Polytes chooses to do based on his personality, needs, and the current situation. In V1, Utility AI evaluates different factors to choose between idling and walking.
    

### 3. OS Integration

Connects Polytes to the computer environment, allowing him to interact with the system and its interfaces rather than existing as an isolated character on the screen.

- **User Interaction:** Defines how the user can directly interact with and control Polytes.
    
    - **Drag:** Allows the user to grab and move Polytes, with his body responding to the interaction.
        
    - **Creator Window:** Provides an interface for creating and customizing Polytes.
        
- **System Integration:** Connects Polytes to the operating system's underlying processes and mechanisms.
    
    - **Process:** Defines how Polytes interacts with operating-system processes, including the use of a separate process associated with the stickman.
        

## v2 Scope

When we say "v2", we are referring to all upcoming v1.x.0 releases, not a single update.

The v2 scope consists of 12 subpillars and 12 sub-subpillars distributed across the three main pillars. Each subpillar and sub-subpillar will contain multiple features.

Together, these define the full scope of v2 and the features to be developed across the upcoming v1.x.0 releases.