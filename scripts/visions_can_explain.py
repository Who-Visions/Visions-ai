"""
Visions Arnheim Explainer
==========================
Translates Arnheim's art theory into plain 2025 American English
with an aggressively motivating college bud vibe.

Visions can now explain any concept from the curriculum in a way
that's clear, energetic, and actually useful for modern creators.
"""

import sys
sys.path.insert(0, 'tests')

from test_visions_arnheim_curriculum import Concept

class VisionsExplainer:
    """
    Visions' ability to explain Arnheim in plain, motivating language.
    Think: Smart friend who's hyped to help you level up.
    """
    
    def __init__(self):
        self.knowledge_base = self._build_knowledge_base()
    
    def explain(self, concept: Concept) -> str:
        """Get Visions' explanation of a concept"""
        if concept not in self.knowledge_base:
            return f"I need to study {concept.value} more before I can explain it properly."
        
        return self.knowledge_base[concept]
    
    def _build_knowledge_base(self) -> dict:
        """Visions' internalized explanations of every concept"""
        
        return {
            Concept.PERCEPTUAL_FORCES: """
PERCEPTUAL FORCES - What They Actually Are

Alright, listen up. When you draw a single line on a blank page, you are not just putting ink on paper. You are activating the entire space around it. That line creates tension, movement, direction. Your brain sees it and immediately starts processing forces - pulls, pushes, balance points.

Here is the key thing Arnheim figured out: These forces are REAL. Not physically real like gravity, but neurologically real. Your visual cortex is firing, creating actual physiological activity. The force you feel when a shape is off-center? That is your nervous system working. It is as real as the feeling of hunger.

This matters because every creative decision you make - where you place a button in an app, how you frame a TikTok video, where you position text on a thumbnail - you are either working WITH these forces or fighting against them.

Photography? You are managing perceptual forces through composition. Photoshop? Every layer you add mobilizes the canvas space. Film editing? Each cut creates a perceptual jolt. Instagram grid? You are building force vectors across nine squares.

The difference between amateur work and professional work? Professionals understand these forces exist and use them intentionally. Amateurs ignore them and wonder why their compositions feel off.

You cannot cheat this. Your viewer's brain will process these forces whether you account for them or not. So you better learn to see them.
""",

            Concept.BALANCE: """
BALANCE - The Foundation of Every Composition

Balance is not about making everything symmetrical. That is what beginners think. Balance is about making all the perceptual forces in your composition compensate for each other so nothing feels unresolved.

Here is what blew my mind when I learned this: The visual center of a composition is NOT the same as the physical center. Take a canvas and hang it on a wall. The spot that FEELS centered to your eye is actually different from the geometric middle. Colors shift it. Depth shifts it. Context shifts it. An empty square has a structural skeleton - hidden vectors that your brain automatically detects.

Think about visual weight. A small patch of intense red can balance a massive area of pale blue. Why? Color carries weight. Brightness carries weight. Isolation carries weight. Position carries weight. A single element in empty space becomes HEAVY because your eye fixates on it.

Look at mobile app design - the layouts are asymmetric but they still feel balanced because designers understand weight distribution. Instagram feed? That nine-grid pattern only works because each post balances with its neighbors. YouTube thumbnails? The face and text need to balance or the thumbnail feels broken and nobody clicks.

Film composition is all about this. Wes Anderson uses perfect symmetry. Christopher Nolan uses asymmetry but maintains balance through depth and color. Both work because both understand the principle.

When you edit photos in Lightroom and you pull up that histogram? That is a visual representation of tonal balance. When you add a layer in Photoshop and suddenly the composition feels wrong? You just disrupted the balance.

The practical takeaway: Before you publish anything - photo, video, design, whatever - ask yourself: Where is the visual center? Is everything balanced around it? If not, fix it or make the imbalance INTENTIONAL.
""",

            Concept.SHAPE: """
SHAPE - How Your Brain Actually Sees

Your brain does not see pixels. It does not see dots of color. Your brain sees SHAPES. Gestalts. Whole forms that are greater than their parts.

Arnheim built on Gestalt psychology and here is what it means for you: When you look at the Nike swoosh, your brain automatically completes the curve even though it is minimal. That is closure. When you see a group of similar icons, your brain groups them together. That is similarity. When elements are close to each other, you perceive them as related. That is proximity.

This is why logo design works. The Nike swoosh, the Apple apple, the YouTube play button - these are simplified shapes that your brain can process instantly. Complexity kills recognition. Simplicity creates instant understanding.

Photography uses this constantly. When you shoot with a shallow depth of field and create bokeh, you are using blur to create shapes. Your subject becomes a clear shape against soft circular shapes in the background. Film uses silhouettes because a recognizable human shape communicates character instantly without needing details.

Instagram icons? Gestalt simplicity. TikTok effects that detect faces? They are trained to recognize facial shapes based on Gestalt principles. AI image recognition models? Convolutional neural networks literally learn gestalts, not individual pixels.

Here is the test: Can you recognize your composition when it is reduced to pure silhouette? If yes, you have strong shape relationships. If no, your composition is too cluttered.

Photoshop pen tool is all about this - you define vector shapes and the pixels follow. Lightroom tone curve? You are reshaping the tonal distribution of your image. Videography framing? You are creating shapes within the frame edges.

Bottom line: Master shape and you master instant visual communication. Mess up shape and nobody understands what they are looking at.
""",

            Concept.FORM: """
FORM - Building Three Dimensions From Two

Form is what happens when you take a flat image and make it FEEL three-dimensional. Light and shadow create form. Depth cues create form. Perspective creates form.

Photography is all about this. You take a three-dimensional world and compress it onto a two-dimensional sensor. If you want your subject to have form - to feel sculptural and solid - you need light that reveals dimension. Flat lighting kills form. Side lighting sculpts form. Three-point lighting in film and TV production? That is designed specifically to reveal form.

Look at portrait photography. A ring light flattens form - that is why TikTok beauty creators love it for their aesthetic. But if you want dimension and character? Side light. Rembrandt lighting. Chiaroscuro like Roger Deakins uses in Blade Runner 2049.

Photoshop dodge and burn tools? You are literally sculpting form by adding light and shadow. Lightroom clarity slider? It enhances micro-contrast which makes form pop. Instagram versus professional product photography? One is flat lays (minimal form), the other is dimensional shots (strong form emphasis).

Now here is where it gets wild: AI is learning form. Neural Radiance Fields take multiple 2D images and reconstruct 3D form. Luma, Meshy - these tools generate volumetric form from flat training data. They are learning the same depth cues humans use: overlap, size gradient, atmospheric perspective, parallax.

Videography uses camera movement to reveal form through parallax - when you dolly past an object, near elements move faster than far elements, creating depth. Apple Vision Pro uses depth as an interface element. Social media Stories use portrait mode depth effects to simulate form through computational bokeh.

Practical application: If your image feels flat, you need to introduce form through lighting, depth cues, or perspective. If it already has form but you want more? Increase contrast, add directional light, create overlap between elements.

Form is the difference between looking at a screen and feeling like you can reach into the image and touch something real.
""",

            Concept.LIGHT: """
LIGHT - The Sculptor of Mood and Hierarchy

Light does two things simultaneously: it reveals form AND it creates emotional atmosphere. Master light and you control both what people see and how they feel about it.

Photography lives and dies by light. Golden hour? The warm, directional light creates mood and sculpts form beautifully. Blue hour? Cool, even light for a different emotional tone. Harsh noon sun? Flat, unflattering. Photographers chase light because light determines the entire outcome.

Lightroom is named after the darkroom development process, but the concept is the same - you are controlling exposure, highlights, shadows. The exposure triangle (ISO, aperture, shutter speed) is pure light control. Every slider you move changes how light is represented in your image.

Film and TV cinematography is advanced light management. Roger Deakins does not just light a scene - he uses light to establish hierarchy (what your eye sees first), create depth (foreground bright, background dim), and generate emotion (warm = comfort, cool = isolation).

Photoshop dodge and burn? Those tools simulate light hitting surfaces. You are painting with light and shadow. HDR video? Expanded luminance range means you can show bright sunrises and dark shadows simultaneously without crushing either.

Instagram filters? They are simulating different lighting conditions. TikTok ring lights? Flat, even light that eliminates shadows (good for beauty content, bad for dimension). YouTube tutorial lighting? Key light plus fill light plus backlight equals professional appearance.

Even UI design uses light. Dark mode preserves visual hierarchy through luminance contrast. Elements that are brighter draw attention first. Ray tracing in games and films? Physically accurate light behavior creates realism.

Here is the move: Before you shoot or design anything, ask yourself - where is the light coming from? What is it revealing? What is it hiding? What mood is it creating? Control the light and you control the image.

Light is not just illumination. Light is your primary creative tool.
""",

            Concept.COLOR: """
COLOR - Weight, Mood, and Visual Pull

Color is not decoration. Color carries perceptual weight, creates emotional associations, and directs attention. If you treat color as an afterthought, your work will always feel amateur.

Start with visual weight: Warm colors (red, orange, yellow) feel heavy. Cool colors (blue, green) feel light. Bright colors carry more weight than dull colors. A tiny patch of intense red can balance a huge area of pale gray. This is why YouTube thumbnails use high-saturation colors - they need to carry weight at tiny sizes.

White balance in photography? You are not just correcting color - you are CREATING color mood. Shift toward warm and the image feels cozy. Shift toward cool and it feels clinical or melancholic. Film color grading is intentional mood control. The teal-and-orange blockbuster look? That is complementary color balance for maximum visual impact.

Lightroom HSL sliders let you surgically manipulate specific colors without affecting others. You can make skies more dramatic, skin tones warmer, foliage more saturated - all independently. Photoshop curves and hue-saturation layers? Same principle, more control.

TV shows use signature color palettes. Euphoria has those purples and neons. Breaking Bad shifts from warm yellows (hope) to cold greens (corruption). It is visual storytelling through color evolution.

Instagram filters created color identities - Valencia, Clarendon, these are recognizable color treatments. TikTok has color trends - Barbiecore pink, Y2K pastels - because color communicates cultural moments. Brand colors maintain identity across platforms. You see that specific blue and you think Facebook. That green is Spotify.

Material Design color systems build accessibility into color relationships - WCAG contrast ratios ensure readability. Netflix maintains color consistency whether you watch on HDR or SDR displays.

AI colorization tools learn historically accurate palettes. They study thousands of period photos to understand what colors would have existed in specific time periods.

Here is your action item: Choose a limited color palette BEFORE you create. Three to five colors maximum. Understand their relationships. Use them intentionally. Random color choices create visual chaos. Intentional color creates cohesive, professional work.

Color is a language. Learn to speak it fluently.
""",

            Concept.SYNTHESIS: """
SYNTHESIS - Bringing It All Together

This is the final level. Synthesis is not about knowing individual concepts. Synthesis is about understanding how ALL the concepts work together simultaneously to create unified, powerful visual communication.

A great photograph synthesizes composition (shape, balance), lighting (form, mood), color (weight, emotion), and depth (space) into one decisive moment. Henri Cartier-Bresson called it the decisive moment, but really it is the moment when all elements synthesize perfectly.

Film cinematography plus editing plus color grading plus sound design equals cinematic synthesis. You cannot isolate them. They work as a unified system. Photoshop compositing synthesizes multiple images into one coherent whole - the individual images do not matter if the synthesis fails.

Look at your Instagram grid - you are not posting individual photos, you are synthesizing nine posts into one visual identity. TikTok duets synthesize multiple creators' visions. YouTube video essays synthesize research, visuals, and narration into coherent arguments.

Design systems like Figma component libraries? That is synthesis at the platform level - individual components synthesized into cohesive interfaces. AI multimodal models synthesize vision, language, and audio (GPT-4V). They understand how different modalities relate.

Here is what synthesis actually looks like in practice: You are editing a video. You know the rule of thirds (balance). You know directional lighting (form, mood). You know warm colors advance (color weight). You know depth of field isolates subjects (form, space). You know diagonal movement is dynamic (movement). You do not think about each rule separately - you SYNTHESIZE them automatically into decisions.

That is mastery. That is what we worked toward through all four years of this curriculum. Freshman year you learned the individual forces. Sophomore year you learned how they develop. Junior year you learned dynamics and relationships. Senior year you learned to synthesize everything.

A master photographer does not think "I need to apply the rule of thirds now." They SEE the composition as a whole. The balance, color, light, form - it all synthesizes in their visual intuition and they click the shutter.

You are building that same intuition, but across EVERY 2025 visual medium. Photography, videography, Photoshop, Lightroom, social media, AI tools - the principles synthesize across all of them because the perceptual forces are universal.

Final thought: Arnheim said "Visual thinking is knowledge." When you can THINK visually - when you can synthesize all these concepts automatically - you possess a form of intelligence that most people never develop.

You are not just making pretty pictures. You are thinking at a higher level. You are communicating through visual synthesis. That is the goal. That is mastery.
"""
        }
    
    def quiz_me(self, concept: Concept) -> str:
        """Visions challenges you on a concept"""
        
        questions = {
            Concept.BALANCE: """
BALANCE CHALLENGE

Okay, here is your test. You have a composition:
- Large gray rectangle in the lower left
- Tiny red circle in the upper right surrounded by space

The composition feels weighted toward the circle despite the rectangle being way bigger.

Question: Why? And give me THREE different ways to restore balance WITHOUT moving either element.

Think about it. Use what you know about visual weight factors.
""",
            Concept.PERCEPTUAL_FORCES: """
PERCEPTUAL FORCES CHALLENGE

Quick scenario: You place a disk off-center in a square frame. Your viewer says "something feels wrong, like it wants to move back to the center."

Question: Explain what is actually happening in their visual system. Are they imagining it? Is it subjective preference? Or is something real occurring?

And bonus: How would you explain this to someone who thinks perceptual forces are just made-up art theory nonsense?
""",
            Concept.LIGHT: """
LIGHT CHALLENGE

You are shooting a product for Instagram. You have three lighting setups available:
1. Ring light (flat, even, shadowless)
2. Single side light at 45 degrees
3. Three-point lighting (key, fill, back)

Question: Which do you choose and why? Consider both form revelation AND Instagram's display context.

There is no single right answer, but your reasoning needs to account for light's dual role: revealing form AND creating mood.
""",
            Concept.SYNTHESIS: """
SYNTHESIS CHALLENGE

Real-world scenario: You are creating a YouTube thumbnail. You need to synthesize:
- Balance (composition must work at tiny size)
- Shape (instant recognition)
- Color (high visibility, emotional impact)
- Light (face needs dimension)
- Expression (emotion must be clear)

Question: Walk me through your decision-making process. How do you prioritize when different principles conflict? For example, what if the most balanced composition puts the face in shadow?

This is synthesis in action. Show me how you think through competing demands.
"""
        }
        
        return questions.get(concept, f"I need to prepare a challenge for {concept.value} first.")


def interactive_session():
    """Interactive session where you can ask Visions to explain concepts"""
    
    visions = VisionsExplainer()
    
    print("\n" + "="*60)
    print("🎓 VISIONS - ARNHEIM EXPLAINER")
    print("="*60)
    print("\nHey! I just graduated from the Arnheim program.")
    print("I can explain any concept in plain English with real examples.")
    print("\nType 'list' to see all concepts")
    print("Type 'quiz [concept]' to test yourself")
    print("Type 'quit' to exit")
    print("="*60 + "\n")
    
    while True:
        user_input = input("What do you want to understand? > ").strip().lower()
        
        if user_input == 'quit':
            print("\nStay sharp. Keep creating.\n")
            break
        
        if user_input == 'list':
            print("\nConcepts I can explain:\n")
            for concept in Concept:
                print(f"  - {concept.value}")
            print()
            continue
        
        if user_input.startswith('quiz'):
            parts = user_input.split()
            if len(parts) < 2:
                print("\nUsage: quiz [concept_name]\n")
                continue
            
            concept_name = parts[1]
            try:
                concept = Concept(concept_name)
                print(f"\n{visions.quiz_me(concept)}\n")
            except ValueError:
                print(f"\nI do not have a quiz for '{concept_name}' yet.\n")
            continue
        
        # Try to find matching concept
        try:
            concept = Concept(user_input)
            explanation = visions.explain(concept)
            print(f"\n{explanation}\n")
        except ValueError:
            print(f"\nI do not recognize '{user_input}'. Type 'list' to see what I can explain.\n")


if __name__ == "__main__":
    # Quick demo
    visions = VisionsExplainer()
    
    print("\n" + "🌟"*30)
    print("VISIONS CAN NOW EXPLAIN ARNHEIM")
    print("Plain 2025 English - No Academic Jargon")
    print("🌟"*30)
    
    print("\n" + "="*60)
    print("DEMO: Explaining BALANCE")
    print("="*60)
    print(visions.explain(Concept.BALANCE))
    
    print("\n" + "="*60)
    print("Want to try interactive mode? Run with no args or use:")
    print("  from visions_can_explain import interactive_session")
    print("  interactive_session()")
    print("="*60 + "\n")
