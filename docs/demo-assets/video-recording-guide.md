# GymPulse Demo Video Recording Guide

## Video Specifications
- **Duration**: 3-5 minutes maximum
- **Format**: MP4, 1920x1080 (1080p)
- **Frame Rate**: 30 FPS minimum
- **Audio**: Clear narration with consistent volume
- **Quality**: Professional screen recording with smooth transitions

---

## Recording Setup Checklist

### Technical Preparation
- [ ] **Screen Recording Software**: OBS Studio or similar high-quality capture
- [ ] **Audio Setup**: External microphone or high-quality headset
- [ ] **Display Settings**: Set to 1920x1080 resolution for clean recording
- [ ] **Browser Setup**: Full-screen browser window, zoom level 100%
- [ ] **Demo Environment**: All services running and responsive

### Demo Environment Validation
- [ ] **Frontend Running**: http://localhost:5173 - Vite dev server responsive
- [ ] **Simulator Active**: 15 machines publishing data across 2 branches
- [ ] **AWS Services**: API Gateway, Lambda, DynamoDB operational via CloudWatch
- [ ] **Chat API**: https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod/chat working
- [ ] **Location Permissions**: Browser geolocation enabled for demo

### Content Preparation
- [ ] **Demo Script**: Memorized 5-minute presentation flow
- [ ] **Backup Screenshots**: Key screens captured for fallback
- [ ] **Timing Practice**: Presentation rehearsed multiple times
- [ ] **Technical Depth**: Q&A responses prepared for key innovations

---

## Video Structure & Narration Script

### Opening Sequence (30 seconds)
**Visual**: Title slide → Architecture diagram
**Narration**:
"Welcome to GymPulse - solving Hong Kong's 24/7 gym equipment availability problem. Members arrive to find their planned machines occupied, wasting time and disrupting workouts. Our solution provides real-time, per-machine availability with AI-powered recommendations that answer 'leg day nearby?' with ETA-optimized suggestions."

**Key Points**:
- Problem statement with Hong Kong context
- Solution overview with AI emphasis
- Architecture diagram showing AWS service integration

### Live System Demo (2 minutes 30 seconds)

#### Sequence 1: Real-Time Machine Tiles (45 seconds)
**Visual**: Frontend showing branch selector → machine grid → live updates
**Narration**:
"Here's our live availability system - 15 machines across Central and Causeway Bay branches. Watch as our IoT simulator changes machine status from free to occupied. Notice the sub-15-second latency from device to UI - that's our real-time pipeline working: IoT Core, Lambda processing, DynamoDB updates, and WebSocket streaming."

**Key Technical Points**:
- Real-time data flow demonstration
- P95 latency achievement (<15s)
- AWS service integration in action

#### Sequence 2: Smart Alert System (30 seconds)  
**Visual**: Click "Notify when free" → show alert configuration → simulate alert trigger
**Narration**:
"Users subscribe to alerts for occupied machines. Our system respects quiet hours and cooldown periods. Watch as this machine becomes free and triggers an immediate notification. The alert system integrates with our real-time pipeline for instant availability updates."

#### Sequence 3: AI Chatbot with Tool-Use (75 seconds)
**Visual**: Open chat → enable location → type "I want to do legs nearby" → show structured response
**Narration**:
"Now the innovation - our agentic chatbot powered by Bedrock Converse API. I'll enable location sharing and ask 'I want to do legs nearby.' The AI agent calls our availability tool, queries real machine data, calculates ETAs using Amazon Location Service, and returns ranked recommendations. This is deterministic tool-use with structured JSON schemas - not just language generation."

**Key Innovation Points**:
- Bedrock Converse API with tool-use capabilities
- Real data integration (not mock responses)
- Cross-service orchestration (Bedrock + Location + DynamoDB)
- Intelligent ranking by ETA and availability

#### Sequence 4: Complete User Journey (20 seconds)
**Visual**: Click recommended branch → navigate to machine details → show category breakdown
**Narration**:
"Seamless integration guides users from query to action. Click the recommendation to view detailed machine availability by category. This completes the user journey from 'leg day nearby?' to actionable gym choice."

### AI Development Showcase (60 seconds)
**Visual**: Switch to code editor → show git commits → display AI evidence
**Narration**:
"This system was built with extensive Amazon Q Developer assistance. 65% of our 15,000 lines were AI-generated - from complete CDK infrastructure to Lambda functions to React components. Here's our git history showing 20 commits with AI attribution. Q Developer generated our IoT processing logic, Bedrock integration, security configurations, and comprehensive test suites. Human refinement focused on gym-specific business logic, performance optimization, and architectural decisions."

**Key Evidence Points**:
- Quantitative metrics (65% AI generation)
- Git commit evidence with proper attribution
- Component breakdown showing AI vs human contributions
- Technical innovation through AI-human collaboration

### Technical Performance Summary (20 seconds)
**Visual**: CloudWatch dashboards → performance metrics
**Narration**:
"Performance validated: P95 latency under 15 seconds end-to-end, chatbot responses under 3 seconds, 50 concurrent devices sustained without drops. This demonstrates production-ready scalability through AI-assisted development."

### Closing (10 seconds)
**Visual**: Return to architecture diagram → final slide
**Narration**:
"GymPulse: Real-time gym availability with AI recommendations. Built in 32.5 hours with 65% AI code generation. Thank you."

---

## Recording Best Practices

### Visual Quality
- **Clean Desktop**: Hide unnecessary windows and applications
- **Full Screen**: Use full browser window for maximum visibility
- **Smooth Transitions**: Practice fluid navigation between features
- **Highlight Interactions**: Use cursor highlighting for important clicks
- **Readable Text**: Ensure all code and UI elements are clearly visible

### Audio Quality
- **Clear Narration**: Speak slowly and clearly
- **Consistent Volume**: Maintain steady audio levels throughout
- **Professional Tone**: Confident delivery with technical precision
- **Eliminate Background**: Record in quiet environment
- **Practice Timing**: Rehearse to fit 3-5 minute constraint

### Technical Demonstration
- **Live System**: Use actual running system, not mock data
- **Real Interactions**: Demonstrate genuine AI responses, not scripted
- **Error Handling**: Have backup plan if live demo fails
- **Performance Evidence**: Show actual metrics and response times
- **Innovation Focus**: Highlight novel technical achievements

---

## Backup Scenarios

### Technical Failure Recovery
1. **Network Issues**: Pre-recorded segments for critical demonstrations
2. **API Failures**: Screenshot walkthrough with technical explanation
3. **Browser Problems**: Alternative browser setup ready
4. **Simulation Failure**: Static data demonstration with narration

### Content Alternatives
- **Detailed Code Walkthrough**: If live demo fails, show code structure
- **Architecture Deep-Dive**: Focus on technical innovation and AI integration
- **Evidence Showcase**: Emphasize comprehensive AI development documentation
- **Performance Metrics**: Highlight quantitative achievements and validation

---

## Post-Recording Checklist

### Video Quality Review
- [ ] **Duration**: Fits within 3-5 minute requirement
- [ ] **Audio Quality**: Clear narration throughout
- [ ] **Visual Clarity**: All text and interactions visible
- [ ] **Technical Accuracy**: All demonstrated features working correctly
- [ ] **Innovation Emphasis**: AI contribution clearly highlighted

### Content Validation
- [ ] **Problem Statement**: Clearly articulated
- [ ] **Solution Demonstration**: Complete user journey shown
- [ ] **Technical Innovation**: AI-assisted development evidence
- [ ] **Performance Validation**: Metrics and scalability demonstrated
- [ ] **Call to Action**: Clear conclusion with project value

### Export Settings
- [ ] **Format**: MP4 with H.264 encoding
- [ ] **Resolution**: 1920x1080 (1080p)
- [ ] **Frame Rate**: 30 FPS minimum
- [ ] **Bitrate**: High quality for clear technical demonstration
- [ ] **File Size**: Optimized for upload requirements

---

## Success Criteria

✅ **Complete System Demo**: All core features demonstrated live  
✅ **AI Evidence Showcased**: Development process and code generation clear  
✅ **Technical Innovation**: Novel Bedrock tool-use and architecture highlighted  
✅ **Professional Quality**: Clear audio, smooth visuals, confident delivery  
✅ **Time Constraint**: 3-5 minutes with complete coverage  
✅ **Backup Ready**: Alternative content prepared for technical issues  

**Recording Target**: Professional demonstration of technical innovation with comprehensive AI development evidence suitable for hackathon judging.