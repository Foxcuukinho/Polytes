# Decision (Behavior Arbitration)

Unlike V1, which relied solely on Utility AI to make decisions, V2 will have a custom decision-making system that will also use Utility AI. Decision-making is divided into 2 systems: Internal Decision (I.D) and Environmental Interference (E.I). They are explained below:

## Internal Decision

It represents what the stickman intrinsically wants to do, regardless of what it can or cannot do at that moment. To ensure greater dynamism, we have a hierarchy:

### Objective

First, the stickman will choose an objective based on its needs and the surrounding environment. Some examples are:

- Go to a place
- Rest
- Play
- 
Objectives can contain _parameters_ that specify how or where they should be carried out. For example:

- Go to: _Window_
- Rest: location: _Taskbar_; posture: _Sitting_

Additionally, an objective can define a sequence of states or sub-objectives that guide the stickman toward achieving its main objective.

**Example:**

- **Main objective:** _Rest_
- **Sequence of sub-objectives:**
    
    1. _Go to Window_
    2. _Sit on Window_
        

### State

States represent what the stickman is currently doing, such as walking, standing still, sitting, or climbing. They are the actions performed to achieve its objectives.

## Environmental Interference

In short, the E.I checks whether the stickman can do what the I.D decided, taking into account its physical state and the conditions it is currently in.

For example, if it wants to rest but is falling, the E.I interferes with the decision, preventing it from resting at that moment. It can also set a new objective to handle the situation, such as _Fall with security_.

It is important to distinguish _Perception_ from the E.I: _Perception_ represents what the stickman perceives from its surroundings, while the E.I deals with the physical conditions that affect it involuntarily and the limitations they impose on its actions.