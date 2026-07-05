# 🤖 WhatsApp Fashion AI Agent

An AI-powered conversational fashion sales assistant that transforms WhatsApp into an intelligent e-commerce platform capable of understanding customer requests, recommending products, sending product images, answering questions naturally, processing orders, and seamlessly handing conversations over to human staff when necessary.

The project combines Artificial Intelligence, Large Language Models (LLMs), Meta WhatsApp Cloud API, Flask, SQLite, and a modern web-based administration console into a complete conversational commerce solution.

---

# Project Overview

Traditional WhatsApp businesses often respond manually to hundreds of customer enquiries every day. Customers repeatedly ask:

* Do you have this dress?
* How much is it?
* What colours are available?
* Can I see another picture?
* Do you have my size?
* How do I pay?
* Where is my order?

Responding manually creates delays, inconsistent customer experiences, and limits business scalability.

This project solves that problem by engineering an intelligent AI sales assistant capable of handling the majority of customer interactions autonomously while allowing human staff to intervene whenever necessary.

---

# Key Features

## AI Fashion Sales Assistant

The assistant understands natural language rather than relying on fixed keyword matching.

Customers can ask questions conversationally such as:

* Show me red gowns
* I need something for a wedding
* Do you have handbags?
* Send another picture
* How much is the emerald dress?
* I want size XL

The AI searches the product catalogue, identifies the most relevant products, and generates intelligent responses.

---

## Intelligent Product Search

The search engine combines:

* SQL filtering
* Tokenised keyword matching
* Product scoring
* Category matching
* Colour matching
* Size matching
* Description similarity

This provides far better search results than simple database lookups.

---

## WhatsApp Cloud API Integration

The application communicates directly with Meta's WhatsApp Cloud API.

Supported capabilities include:

* Receiving customer messages
* Sending AI responses
* Sending product images
* Sending order confirmations
* Manual staff replies
* Webhook verification

---

## Product Catalogue Management

Administrators can:

* Add products
* Edit products
* Delete products
* Upload product images
* Update stock
* Mark featured products
* Manage categories
* Manage colours
* Manage sizes

All updates immediately become available to the AI.

---

## Image Delivery

Products support multiple images.

The AI automatically sends product images whenever customers request:

* picture
* image
* photo
* show me
* another picture

Both external image URLs and locally uploaded images are supported.

---

## Story Catalogue

Products can be linked to WhatsApp Status stories.

Customers asking questions such as:

> "How much is the dress from today's status?"

can receive intelligent responses because the AI maintains relationships between story posts and products.

---

## Human Handoff

Staff members can:

* Pause AI
* Resume AI
* View conversations
* Reply manually

When AI is paused for a customer, human operators take complete control of the conversation.

---

## Customer Memory

The assistant stores:

* customer names
* addresses
* conversation history
* previous interactions
* AI pause state

allowing contextual conversations.

---

## Order Processing

Customers can place orders directly through WhatsApp.

Orders contain:

* products
* quantities
* subtotal
* delivery fee
* payment status
* customer information

The system automatically stores orders inside the database.

---

## Backend Administration Console

A modern browser dashboard provides:

* Product management
* Conversation monitoring
* Order monitoring
* Story management
* AI controls
* Product image uploads
* Chat simulator
* System health monitoring

---

# Technology Stack

## Backend

* Python
* Flask
* SQLite
* Gunicorn

---

## Frontend

* HTML5
* CSS3
* Vanilla JavaScript

---

## Artificial Intelligence

* OpenAI GPT models
* Prompt Engineering
* Context-aware conversation management

---

## APIs

* Meta WhatsApp Cloud API
* OpenAI API

---

## Database

SQLite

Tables include:

* products
* story_items
* customers
* conversations
* orders

---

# AI Workflow

Customer Message

↓

Webhook

↓

Message Parser

↓

Conversation Memory

↓

Product Search Engine

↓

Prompt Engineering

↓

LLM Response Generation

↓

WhatsApp Cloud API

↓

Customer

---

# Engineering Highlights

The project demonstrates practical implementation of:

* Conversational AI
* Retrieval-Augmented Generation (RAG)-style product retrieval
* REST API design
* Database engineering
* AI prompt engineering
* Context management
* Image handling
* Webhook architecture
* Business workflow automation
* CRUD operations
* Production deployment

---

# Deployment

The application is deployed using Render with Gunicorn serving the Flask application.

The backend communicates securely with:

* Meta WhatsApp Cloud API
* OpenAI API

Environment variables are used for all sensitive credentials.

---

# Challenges Solved

During development several engineering challenges were encountered and resolved, including:

* Git history recovery after accidental hard resets
* Render deployment issues
* Gunicorn startup failures
* Dependency conflicts
* Cython import errors
* Webhook verification
* Image upload handling
* Relative versus absolute image URLs
* Persistent storage limitations on Render
* SQLite deployment considerations
* WhatsApp webhook debugging
* AI context improvements
* Product retrieval optimisation

These challenges significantly improved the robustness and maintainability of the final application.

---

# Future Improvements

Planned enhancements include:

* PostgreSQL production database
* Cloudinary image storage
* Payment gateway integration
* Automatic payment verification
* Inventory analytics dashboard
* Customer recommendation engine
* Vector database semantic search
* Voice message understanding
* OCR for payment receipts
* Multi-vendor support
* Admin authentication
* Sales analytics
* Customer segmentation
* Recommendation system
* Docker deployment
* Kubernetes support

---

# Learning Outcomes

This project demonstrates practical experience with:

* Artificial Intelligence
* Machine Learning integration
* Large Language Models
* Prompt Engineering
* Full Stack Development
* REST APIs
* Cloud Deployment
* Meta Developer Platform
* Database Design
* Production Debugging
* Git Version Control
* Conversational Commerce

---

# Author

**Badawi Aminu Muhammed**

Data Scientist | AI & Machine Learning Engineer | M&E Analytics Specialist


