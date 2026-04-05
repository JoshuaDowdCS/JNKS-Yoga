"use client";

import Link from "next/link";
import { TextAnimate } from "@/components/ui/text-animate";
import { ShimmerButton } from "@/components/ui/shimmer-button";
import { BlurFade } from "@/components/ui/blur-fade";
import { useAccentColor } from "@/components/accent-color-provider";


export function HeroSection() {
  const { accent } = useAccentColor();

  return (
    <section className="relative py-12 sm:py-20">
      <div className="mx-auto max-w-6xl px-6">
        <div className="flex flex-col items-center gap-8 lg:gap-12">
          <div className="text-center space-y-6 max-w-3xl">
            {/* Yoga-themed visual */}
            <div className="relative mx-auto h-[200px] w-[200px] sm:h-[260px] sm:w-[260px]">
              {/* Ambient glow */}
              <div className="absolute inset-0 -inset-x-16 -inset-y-16 rounded-full blur-3xl" style={{ backgroundColor: `rgba(${accent.rgb}, 0.1)` }} />
              <div className="absolute inset-0 -inset-x-8 -inset-y-8 rounded-full blur-2xl" style={{ backgroundColor: `rgba(${accent.rgbDark}, 0.05)` }} />
              {/* Lotus / yoga silhouette */}
              <div className="relative h-full w-full flex items-center justify-center">
                <svg viewBox="0 0 200 200" className="w-full h-full text-primary opacity-80" fill="none" stroke="currentColor" strokeWidth="1.5">
                  {/* Meditation figure silhouette */}
                  <circle cx="100" cy="55" r="15" strokeWidth="2" />
                  <path d="M100 70 L100 120" strokeWidth="2" />
                  <path d="M100 85 L70 105" strokeWidth="2" />
                  <path d="M100 85 L130 105" strokeWidth="2" />
                  <path d="M100 120 L70 150" strokeWidth="2" />
                  <path d="M100 120 L130 150" strokeWidth="2" />
                  {/* Lotus petals */}
                  <path d="M60 170 Q80 145 100 170 Q120 145 140 170" strokeWidth="1.5" className="text-primary/60" />
                  <path d="M50 175 Q75 155 100 175 Q125 155 150 175" strokeWidth="1.5" className="text-primary/40" />
                </svg>
              </div>
            </div>

            <TextAnimate
              as="h1"
              by="word"
              animation="blurInUp"
              duration={1}
              className="text-5xl font-bold tracking-tight sm:text-7xl font-heading"
            >
              Perfect Your Yoga Practice
            </TextAnimate>

            <BlurFade delay={0.4} inView>
              <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                Record your practice or upload a video, and get instant AI-powered
                feedback on your yoga form. Know exactly what to improve.
              </p>
            </BlurFade>

            <BlurFade delay={0.6} inView>
              <div className="flex justify-center">
                <Link href="/analyze">
                  <ShimmerButton
                    shimmerColor={accent.hex}
                    shimmerSize="0.08em"
                    background={`rgba(${accent.rgbDark}, 0.85)`}
                    borderRadius="12px"
                    className="px-8 py-4 text-base font-semibold"
                  >
                    Start Analyzing
                  </ShimmerButton>
                </Link>
              </div>
            </BlurFade>
          </div>
        </div>
      </div>
    </section>
  );
}
