# InnerEase AI — MVP Specification

## Overview

InnerEase AI is a trauma-aware AI system designed to help users regulate their nervous system in real time.

Unlike traditional mental health apps, this system does NOT focus on therapy, journaling, or long conversations.

Instead, it provides:

* Immediate emotional understanding
* Body-state awareness
* Short, actionable physical regulation steps



## Problem

Many users:

* Understand their problems logically
* But still feel triggered physically
* Experience stress, anxiety, freeze, or emotional overwhelm

Existing tools focus on:

* Thinking (CBT, reflection)
* Passive tracking

But trauma is stored in the body.


##  Solution

A system that:

1. Detects user emotion from text input
2. Maps emotion → body state
3. Provides 1 short physical regulation action


##  MVP Scope (Version 1)

### Included Features

* Text input from user
* Emotion detection (via AI)
* Predefined mapping:
  emotion → body state → action
* API endpoint: `/analyze`
* Frontend UI:

  * input box
  * submit button
  * result display
* Loading + error states
* Safety fallback (basic)


###  NOT Included (for MVP)

* No authentication
* No database (use JSON or in-memory)
* No user history
* No voice input
* No long conversations
* No therapy-style chatbot
* No analytics

##  Example Flow

### Input:

"I feel overwhelmed and stuck"

### Output:

* Emotion: anxiety / freeze
* Body State: tight chest, low energy
* Action: stand up, shake your body for 20 seconds, then exhale slowly 5 times

##  Core Principles

* Action > Advice
* Body-based > Thought-based
* Short > Long
* Real > Motivational
* Calm > Overly empathetic

##  UI Requirements

* Clean and minimal interface
* Neutral and calming design
* No overwhelming content
* Clear separation:

  * Input
  * Output
  * Action

##  Constraints

* Beginner-friendly code
* Modular structure
* No overengineering
* Easy to run locally

##  Success Criteria

MVP is successful if:

* User can input text
* System returns structured response
* Response includes:

  * emotion
  * body state
  * action
* System runs locally without errors

## Future (Not for MVP)

* Pattern detection
* Personalization
* Voice input
* Real-time intervention triggers
* Mobile app
