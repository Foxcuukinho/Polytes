# Behavior Arbitration (B.A.)

## Overview

Behavior Arbitration is Polytes' decision-making system. It determines how the stickman's intentions, current situation, and environmental influences affect his behavior.  
It contains two main subsystems:

- **Internal Decision (I.D.)** — determines what the stickman wants to do.
- **Environmental Interference (E.I.)** — represents how environmental circumstances and stimuli influence the stickman's intended behavior.  

The goal is to make behavior flexible and context-aware, rather than relying exclusively on predefined states.
    

## Architecture

### 1. Internal Decision (I.D.)

Internal Decision determines the stickman's intentions and organizes them into a hierarchy.

#### Objective

An Objective represents a general intention or goal.  
Examples:

- `Rest`
- `Play`
- `Go to

Objectives describe what the stickman wants to accomplish, rather than the exact behavior used to accomplish it.

#### Parameters

Parameters provide additional information required by an Objective.  
For example, `Go to` could have a `target` parameter specifying the destination.  
Different Objectives may require different parameters.

#### Desired State

The Desired State represents the condition the stickman wants to reach while pursuing an Objective. It connects the general intention to the behavior needed to accomplish it.

#### State

The State represents the stickman's current behavior or condition. Examples include `IDLE` and `WALK`.  
The State should not be treated as the entirety of the stickman's behavior. Additional details can exist independently of it.

#### State Detail

State Detail represents behavioral details that can vary without necessarily changing the main State.  
For example, a stickman could be walking while looking at an object or turning his head toward something interesting.  
This separation allows more varied and emergent behavior without requiring a separate State for every possible combination.

#### Satisfaction

`Satisfaction` is a variable used during decision-making to evaluate how advantageous an Objective would be.  
The Internal Decision uses these evaluations to compare available Objectives and choose one.  
Example candidate Objectives:

- `Rest`
- `Play`
- `Go to` 

**The evaluation method is still undefined.** The factors considered, calculation method, alue representation, and comparison rules remain to be determined.
    

### 2. Environmental Interference (E.I.)

Environmental Interference represents how the environment and current stimuli influence the stickman's intended behavior.  
It does not necessarily prohibit an action outright. Environmental circumstances may instead increase or decrease the likelihood that a particular behavior will occur.  
This is intended to preserve flexibility and allow behavior to emerge from the interaction between intentions and circumstances.

#### Stimuli

Stimuli represent relevant events, objects, or circumstances that may influence behavior.  
A preliminary example of how stimuli might be represented:

```
stickman.stimulus = [
    {"stimulus": "Fall", "intensity": 100},
    {"stimulus": "See_Stickman", "intensity": 60}
]
```

The values range from 0 to 100 in this example.  
The precise meaning of `intensity`, how stimuli are generated, how long they remain active, and how they influence decision-making are still undecided.

#### Perception

Perception is a separate system responsible for obtaining information about the environment.  
It detects and identifies relevant things, providing information that can be used by Environmental Interference and other systems.  
Perception does not make the final behavioral decision itself.

## Relationship Between Components

The intended flow is:

1. **Perception** provides information about the environment.
2. **Internal Decision** determines the stickman's intention and evaluates available Objectives.
3. **Environmental Interference** considers environmental circumstances and active stimuli that may influence the intended behavior.
4. **Behavior Arbitration** reconciles these factors and determines the resulting behavior, represented by the current State and its details.
5. The **Animation System** selects an appropriate animation preset based on the resulting behavior and additional factors such as needs and emotional state.  
    This is a conceptual flow. The precise implementation and interaction rules have not yet been defined.
    

## Animation System

The Animation System is separate from Behavior Arbitration.  
It selects animation presets that express the stickman's behavior, needs, and emotional state.  
For example:

- `Walk Sad`
- `Walk Happy`  
    
    
The State and animation preset are different concepts. A stickman can remain in the `WALK` State while using different animation presets depending on his current condition.
    

## Open Questions

The following aspects remain to be defined:

- How `Satisfaction` is calculated and how Objectives are compared.
- How Objectives, Parameters, Desired States, States, and State Details are connected in practice.
- How Environmental Interference modifies or influences intended behavior.
- What stimulus intensity represents and how stimuli are managed.
- How conflicts between intentions and environmental circumstances are resolved.
- How Perception communicates relevant information to the other components.
- How the Animation System chooses between available presets.  

These decisions should be made as the design develops, rather than assuming that the current structure is final.